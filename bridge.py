"""Bounded, authenticated loopback transport. No browser payload logs."""
import hmac
import json
import queue
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from desktop.windows_activity import foreground, BROWSERS

PORT=47831

def make_handler(token,events,state,foreground_fn=foreground):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def setup(self):
            super().setup(); self.connection.settimeout(2)
        def authenticated(self):
            return hmac.compare_digest(self.headers.get('Authorization','').encode('utf-8'), ('Bearer '+token).encode('utf-8'))
        def result(self,code,body=None):
            data=json.dumps(body).encode() if body is not None else b''
            self.send_response(code)
            self.send_header('Content-Type','application/json')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            if not self.authenticated(): self.result(403); return
            if self.path!='/status': self.result(404); return
            epoch=state(); app=foreground_fn()
            self.result(200,{'epoch':epoch if app is None or app in BROWSERS else None})
        def do_POST(self):
            if not self.authenticated(): self.result(403); return
            if self.path!='/context': self.result(404); return
            epoch=state(); app=foreground_fn()
            if not epoch or (app is not None and app not in BROWSERS): self.result(409); return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if self.headers.get('Transfer-Encoding') or not 0<size<=4096: raise ValueError()
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict): raise ValueError()
                title=body['title']; domain=body['domain']; stamp=body['timestamp']
                browser=body['browser']
                if browser not in BROWSERS: raise ValueError()
                if app is not None and app!=browser: self.result(409); return
                if body.get('epoch')!=epoch: self.result(409); return
                if not isinstance(title,str) or not isinstance(domain,str) or len(title)>512 or len(domain)>253 or (not domain and title): raise ValueError()
                if not isinstance(stamp,(int,float)) or isinstance(stamp,bool) or not abs(time.time()*1000-stamp)<5000: raise ValueError()
                if state()!=epoch: self.result(409); return
                events.put_nowait({'source':'browser','browser':browser,'title':title,'domain':domain,'epoch':epoch,'timestamp':stamp})
            except queue.Full: self.result(429); return
            except (ValueError,KeyError,TypeError): self.result(400); return
            self.result(204)
    return Handler

def start_bridge(token,events,state=lambda: None,port=PORT,foreground_fn=foreground):
    server=HTTPServer(('127.0.0.1',port),make_handler(token,events,state,foreground_fn))
    Thread(target=server.serve_forever,daemon=True).start()
    return server
