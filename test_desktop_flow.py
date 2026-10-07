"""Exercise real desktop methods and HTTP parsing without a GUI/socket server."""
import io
import json
import queue
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from desktop.app import App
from desktop.bridge import make_handler
from core.messages import Messages
from core.storage import Store

class DesktopFlowTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.now=0;self.foreground='chrome.exe'
  self.app=App.__new__(App);app=self.app
  app.events=queue.Queue(maxsize=64);app.session=None;app.epoch=None;app.last_browser_stamp=0
  app.messages=Messages();app.prompt_context=None
  app.settings=dict(grace=20,min_interval=90,max_prompts=4,repeated_window=600)
  app.goal=Mock();app.goal.get.return_value='Study algebra'
  app.minutes=Mock();app.minutes.get.return_value='25'
  app.age=Mock();app.age.get.return_value='13+'
  app.root=Mock();app.bubble=Mock();app.canvas=Mock();app.cat_image=1;app.status=Mock()
  app.buttons=Mock();app.buttons.winfo_children.return_value=[]
  app.store=Store(Path(self.temp.name)/'sessions.db')
  self.patches=[patch('desktop.app.foreground',lambda:self.foreground),patch('time.monotonic',lambda:self.now),patch('time.time',lambda:10000+self.now),patch('desktop.app.ttk.Button')]
  for item in self.patches: item.start()
  self.handler=make_handler('test-token',app.events,app.bridge_state,lambda:self.foreground)
  app.start()
 def tearDown(self):
  self.app.store.close()
  for item in reversed(self.patches): item.stop()
  self.temp.cleanup()
 def send(self,title,domain,epoch=None):
  payload={'epoch':epoch or self.app.epoch,'browser':'chrome.exe','title':title,'domain':domain,'timestamp':(10000+self.now)*1000}
  data=json.dumps(payload).encode()
  raw=(f'POST /context HTTP/1.0\r\nAuthorization: Bearer test-token\r\nContent-Length: {len(data)}\r\n\r\n').encode()+data
  class Connection:
   def __init__(self): self.output=bytearray()
   def makefile(self,*args): return io.BytesIO(raw)
   def settimeout(self,value): pass
   def sendall(self,data): self.output.extend(data)
  conn=Connection();self.handler(conn,('127.0.0.1',1),None)
  return int(conn.output.split(b' ')[1])
 def test_complete_distraction_flow_and_summary(self):
  self.assertEqual(self.send('Quadratic equations','youtube.com'),204);self.app.poll()
  self.now=1;self.assertEqual(self.send('Funniest Minecraft','youtube.com'),204);self.app.poll()
  self.now=20;self.app.poll();self.assertEqual(self.app.session.prompts,0)
  self.now=21;self.app.poll();self.assertEqual(self.app.session.prompts,1)
  self.app.answer('no');self.assertEqual(self.app.session.redirects,1)
  self.now=22;self.send('Solving quadratic equations','youtube.com');self.app.poll()
  self.assertIsNone(self.app.session.pending)
  self.assertTrue(self.app.stop(progress_note='Start at question 9'))
  summary=self.app.store.history()[0]
  self.assertEqual(summary['redirects'],1);self.assertEqual(summary['progress_note'],'Start at question 9')
  self.assertNotIn('domain',summary);self.assertNotIn('title',summary)
 def test_switch_to_edge_rejects_queued_chrome_context(self):
  self.send('Minecraft','youtube.com');self.foreground='msedge.exe';self.app.poll()
  self.assertIsNone(self.app.session.pending)
 def test_stale_answer_does_not_approve_new_context(self):
  self.send('Minecraft','youtube.com');self.app.poll();self.now=20;self.app.poll()
  self.app.session.observe('Other title','youtube.com',21)
  self.app.answer('study');self.assertEqual(self.app.session.approved,set())
 def test_break_and_internal_page(self):
  self.send('Minecraft','youtube.com');self.app.poll();self.now=1
  self.send('','');self.app.poll();self.assertIsNone(self.app.session.pending)
  old=self.app.epoch;self.app.take_break();self.assertEqual(self.send('Minecraft','youtube.com',old),409)
  self.now=301;self.app.poll();self.assertEqual(self.app.session.state,'ready')
  self.assertIsNone(self.app.bridge_state());self.app.resume();self.assertNotEqual(self.app.epoch,old)
 def test_failed_save_can_retry(self):
  with patch.object(self.app.store,'save',side_effect=sqlite3.OperationalError('disk full')),patch('desktop.app.messagebox.showerror'):
   self.assertFalse(self.app.stop());self.assertIsNotNone(self.app.session)
  self.assertTrue(self.app.stop());self.assertEqual(len(self.app.store.history()),1)
