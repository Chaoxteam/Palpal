import unittest
from core.classifier import classify, STUDY, DISTRACTION, UNSURE
class ClassifierTests(unittest.TestCase):
 def test_generic_words_are_not_evidence(self):
  self.assertEqual(classify('Finish my math homework','Math videos','youtube.com'),UNSURE)
 def test_mixed_content_is_uncertain(self):
  self.assertEqual(classify('Algebra','Quadratic equations Minecraft prank','youtube.com'),UNSURE)
 def test_intentional_entertainment_subject(self):
  self.assertEqual(classify('Minecraft architecture','Minecraft architecture tutorial','youtube.com'),STUDY)
 def test_apps(self):
  self.assertEqual(classify('Algebra','winword.exe',''),STUDY)
  self.assertEqual(classify('Algebra','steam.exe',''),DISTRACTION)
  self.assertEqual(classify('Algebra','unknown.exe',''),UNSURE)
