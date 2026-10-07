import unittest
from core.engine import *
class Tests(unittest.TestCase):
 def test_relevance(self):
  self.assertEqual(classify('algebra','Quadratic equations','youtube.com'),STUDY)
  self.assertEqual(classify('algebra','Funniest Minecraft','youtube.com'),DISTRACTION)
  self.assertEqual(classify('algebra','A video','youtube.com'),UNSURE)
 def test_grace_cancel(self):
  s=Session('algebra',25,0);s.observe('Minecraft','youtube.com',0)
  self.assertIsNone(s.tick(19));s.observe('Algebra','docs.google.com',19);self.assertIsNone(s.tick(30))
 def test_loop(self):
  s=Session('algebra',25,0);s.observe('Minecraft','youtube.com',0)
  self.assertEqual(s.tick(20),'check');s.answer('no',21);s.observe('Algebra','docs.google.com',22)
  self.assertIsNone(s.tick(100));self.assertEqual(s.redirects,1)
 def test_override(self):
  s=Session('algebra',25,0);s.observe('Video','youtube.com',0);s.answer('study',20)
  self.assertEqual(classify(s.goal,'Video','youtube.com',s.approved),STUDY)
  self.assertEqual(classify('algebra','Video','youtube.com'),UNSURE)
 def test_break(self):
  s=Session('algebra',25,0);s.start_break(10);s.observe('Minecraft','youtube.com',20)
  self.assertIsNone(s.tick(100));self.assertEqual(s.tick(310),'resume');self.assertEqual(s.state,'ready');self.assertEqual(s.elapsed(400)[0],10)
  s.resume(400);self.assertEqual(s.break_seconds,390);self.assertEqual(s.state,'focus')
 def test_cap_cooldown(self):
  s=Session('algebra',25,0,Config(1,90,1));s.observe('Minecraft','youtube.com',0);self.assertEqual(s.tick(1),'check')
  s.observe('Fortnite','youtube.com',2);self.assertIsNone(s.tick(100))
 def test_domain(self):
  self.assertEqual(classify('algebra','Welcome','docs.google.com.evil.test'),UNSURE)

class ExtendedSessionTests(unittest.TestCase):
 def test_break_reminder_once_and_explicit_resume(self):
  s=Session('algebra',25,0);s.start_break(10)
  self.assertEqual(s.tick(280),'break_ending');self.assertIsNone(s.tick(281))
  self.assertEqual(s.tick(310),'resume');s.observe('Minecraft','youtube.com',311)
  self.assertIsNone(s.pending);self.assertEqual(s.elapsed(600),(10,590))
  s.resume(600);self.assertEqual(s.elapsed(610),(20,590))
 def test_repeated_window_expires(self):
  s=Session('algebra',25,0,Config(1,1,10,10))
  for index,start in enumerate([0,3,6]):
   s.observe(str(index),'unknown.test',start)
   self.assertEqual(s.tick(start+1),'reset' if index==2 else 'check')
  s.observe('new','unknown.test',100);self.assertEqual(s.tick(101),'check')
 def test_keep_going_does_not_approve(self):
  s=Session('algebra',25,0);s.observe('Video','youtube.com',0);s.answer('continue',20)
  self.assertEqual(s.approved,set())
