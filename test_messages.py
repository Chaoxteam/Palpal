import unittest
from core.messages import Messages, AGES
class MessageTests(unittest.TestCase):
 def test_age_and_rotation(self):
  for age in AGES:
   messages=Messages();first=messages.choose('check',age,0)
   self.assertNotEqual(first,messages.choose('check',age,100))
 def test_return_silence(self):
  messages=Messages();self.assertTrue(messages.choose('return','13+',0))
  self.assertEqual(messages.choose('return','13+',100),'')
  self.assertTrue(messages.choose('return','13+',200))
