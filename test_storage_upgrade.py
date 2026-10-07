import sqlite3
import tempfile
import unittest
from pathlib import Path
from core.storage import Store

class StorageUpgradeTests(unittest.TestCase):
 def test_old_schema_and_deletion(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'sessions.db';db=sqlite3.connect(path)
   db.execute('CREATE TABLE sessions (id TEXT PRIMARY KEY, goal TEXT NOT NULL, start REAL, end REAL, planned_seconds REAL, focus_seconds REAL, break_seconds REAL, redirects INTEGER, block_completed INTEGER)')
   db.execute("INSERT INTO sessions VALUES ('old','Algebra',1,2,1500,2,0,0,0)");db.commit();db.close()
   store=Store(path);row=store.history()[0]
   self.assertEqual(row['goal_completed'],0);self.assertEqual(row['progress_note'],'')
   store.delete_all();self.assertEqual(store.history(),[]);self.assertIsNone(store.latest());store.close()
 def test_progress_roundtrip(self):
  with tempfile.TemporaryDirectory() as directory:
   store=Store(Path(directory)/'sessions.db')
   store.save(dict(goal='Math',start=1,end=100,planned_seconds=1500,focus_seconds=99,break_seconds=0,redirects=1,block_completed=False,goal_completed=False,progress_note='8 of 12 questions; start at 9'))
   self.assertEqual(store.history()[0]['progress_note'],'8 of 12 questions; start at 9');store.close()
