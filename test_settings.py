import json
import tempfile
import unittest
from pathlib import Path
from core.settings import load_settings

class SettingsTests(unittest.TestCase):
 def test_defaults_and_stable_token(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'settings.json';first=load_settings(path)
   self.assertEqual(load_settings(path),first);self.assertEqual(first['grace'],20)
 def test_invalid_values(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'settings.json'
   for value in [True,float('nan'),-1,'20']:
    path.write_text(json.dumps({'token':'a'*32,'grace':value}))
    with self.assertRaises(ValueError): load_settings(path)
 def test_bad_json_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'settings.json';path.write_text('broken')
   with self.assertRaises(ValueError): load_settings(path)
   self.assertEqual(path.read_text(),'broken')
