import io
import os
import json
import queue
import tempfile
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
from desktop.bridge import start_bridge, make_handler
from core.storage import Store

class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.events=queue.Queue(maxsize=1);self.epoch='session';self.app='chrome.exe'
  self.handler=make_handler('test-token',self.events,lambda:self.epoch,lambda:self.app)

 def request(self,path='/context',body=None,token='test-token'):
  data=json.dumps(body).encode() if body is not None else b''
  method='POST' if body is not None else 'GET'
  raw=(f'{method} {path} HTTP/1.0\r\nHost: 127.0.0.1\r\nAuthorization: Bearer {token}\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\n\r\n').encode()+data
  class Connection:
   def __init__(self): self.output=bytearray()
   def makefile(self,*args): return io.BytesIO(raw)
   def settimeout(self,value): pass
   def sendall(self,data): self.output.extend(data)
  connection=Connection()
  self.handler(connection,('127.0.0.1',12345),None)
  headers,response=bytes(connection.output).split(b'\r\n\r\n',1)
  return int(headers.split(b' ')[1]),response
 def payload(self): return {'epoch':'session','browser':'chrome.exe','title':'Quadratic equations','domain':'youtube.com','timestamp':time.time()*1000}
 def test_authentication(self):
  self.assertEqual(self.request('/status',token='wrong')[0],403)
  self.assertTrue(self.events.empty())
 def test_no_session_or_break(self):
  self.epoch=None
  self.assertIsNone(json.loads(self.request('/status')[1])['epoch'])
  self.assertEqual(self.request(body=self.payload())[0],409);self.assertTrue(self.events.empty())
 def test_foreground(self):
  self.app='game.exe';self.assertEqual(self.request(body=self.payload())[0],409)
  self.assertTrue(self.events.empty())
 def test_epoch_and_stale(self):
  body=self.payload();body['epoch']='old';self.assertEqual(self.request(body=body)[0],409)
  body=self.payload();body['timestamp']-=6000;self.assertEqual(self.request(body=body)[0],400)
 def test_bounded_queue(self):
  self.assertEqual(self.request(body=self.payload())[0],204)
  self.assertEqual(self.request(body=self.payload())[0],429)
  self.assertEqual(self.events.qsize(),1)
 def test_internal_tab_clears_context(self):
  body=self.payload();body['title']='';body['domain']=''
  self.assertEqual(self.request(body=body)[0],204);self.assertEqual(self.events.get()['domain'],'')
 def test_other_browser_rejected(self):
  self.app='msedge.exe';self.assertEqual(self.request(body=self.payload())[0],409)
 def test_malformed(self):
  self.assertEqual(self.request(body=[])[0],400)
  body=self.payload();body['title']='x'*513;self.assertEqual(self.request(body=body)[0],400)

class StorageTests(unittest.TestCase):
 def test_summary_persistence(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'sessions.db';store=Store(path)
   record=dict(goal='Algebra',start=1,end=2,planned_seconds=1500,focus_seconds=1,break_seconds=0,redirects=0,block_completed=False)
   store.save(record);store.close();store=Store(path)
   self.assertEqual(store.latest(),'Algebra')
   columns=[row[1] for row in store.db.execute('PRAGMA table_info(sessions)')]
   self.assertNotIn('title',columns);self.assertNotIn('domain',columns);store.close()

@unittest.skipUnless(os.environ.get('PALPAL_LIVE_TESTS')=='1','Opt-in loopback test: PALPAL_LIVE_TESTS=1')
class LiveBridgeTests(unittest.TestCase):
 def test_loopback(self):
  events=queue.Queue(maxsize=1)
  server=start_bridge('test-token',events,lambda:'session',port=0,foreground_fn=lambda:'chrome.exe')
  try:
   req=Request(f'http://127.0.0.1:{server.server_port}/status',headers={'Authorization':'Bearer test-token'})
   with urlopen(req,timeout=3) as response:
    self.assertEqual(json.load(response),{'epoch':'session'})
  finally: server.shutdown();server.server_close()
