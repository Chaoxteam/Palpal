"""Check lifecycle/gating with simulated Win32 APIs, not native compatibility."""
import ctypes
import queue
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from desktop import windows_activity as activity

class HookFunction:
 def __init__(self,ready,hook=1): self.ready=ready;self.hook=hook;self.callback=None
 def __call__(self,*args):
  self.callback=args[3];self.ready.set();return self.hook

class MonitorTests(unittest.TestCase):
 def run_monitor(self,enabled,hook=1):
  ready=Event();quit_event=Event();self.hook=HookFunction(ready,hook)
  self.user=SimpleNamespace(PeekMessageW=Mock(),SetWinEventHook=self.hook,
   GetMessageW=lambda *args:(quit_event.wait(2) and 0),
   PostThreadMessageW=lambda *args:quit_event.set(),UnhookWinEvent=Mock(),TranslateMessage=Mock(),DispatchMessageW=Mock())
  self.foreground=Mock(return_value='chrome.exe')
  self.patches=[patch.object(activity,'os',SimpleNamespace(name='nt')),patch.object(activity,'user',self.user,create=True),patch.object(activity,'kernel',SimpleNamespace(GetCurrentThreadId=lambda:123),create=True),patch.object(activity.ctypes,'WINFUNCTYPE',ctypes.CFUNCTYPE,create=True),patch.object(activity,'foreground',self.foreground)]
  for item in self.patches:item.start()
  self.events=queue.Queue();monitor=activity.start_monitor(self.events,enabled)
  self.addCleanup(monitor.stop)
  self.assertTrue(ready.wait(2),'Monitor never registered hook')
  return monitor
 def tearDown(self):
  if hasattr(self,'monitor'):self.monitor.stop()
  for item in reversed(getattr(self,'patches',[])):item.stop()
 def test_inactive_does_not_read_context_and_stop_unhooks(self):
  self.monitor=self.run_monitor(lambda:False)
  self.hook.callback(None,3,None,0,0,0,0)
  self.assertEqual(self.foreground.call_count,0);self.assertTrue(self.events.empty())
  self.monitor.stop();self.assertFalse(self.monitor.thread.is_alive());self.user.UnhookWinEvent.assert_called_once_with(1)
 def test_active_records_minimal_event(self):
  self.monitor=self.run_monitor(lambda:True)
  self.hook.callback(None,3,None,0,0,0,0)
  event=self.events.get(timeout=2)
  self.assertEqual(event,{'source':'window','app':'chrome.exe'})
 def test_failed_hook_reported(self):
  self.monitor=self.run_monitor(lambda:True,hook=0)
  self.monitor.thread.join(timeout=2)
  self.assertFalse(self.monitor.available);self.assertTrue(self.events.empty())
  self.user.UnhookWinEvent.assert_not_called()
