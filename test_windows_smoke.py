"""Opt-in real Windows Tk/SQLite/socket smoke test, suitable for CI."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

@unittest.skipUnless(os.name=='nt' and os.environ.get('PALPAL_GUI_TESTS')=='1','Requires opt-in Windows GUI runner')
class WindowsSmokeTests(unittest.TestCase):
    def test_real_desktop_lifecycle(self):
        from desktop.app import App
        from desktop.windows_activity import foreground
        with tempfile.TemporaryDirectory() as directory, patch('desktop.app.DATA',Path(directory)):
            app=App()
            try:
                app.root.update()
                self.assertIsNotNone(app.server)
                self.assertTrue(app.canvas.winfo_exists())
                self.assertIsInstance(foreground(),str)
                app.goal.delete(0,'end'); app.goal.insert(0,'Study algebra')
                app.start(); app.root.update()
                self.assertEqual(app.session.state,'focus')
                app.take_break(); app.root.update()
                self.assertEqual(app.session.state,'break')
                self.assertIsNone(app.bridge_state())
                self.assertTrue(app.stop(progress_note='Start at question 9'))
                self.assertEqual(app.store.history()[0]['progress_note'],'Start at question 9')
            finally: app.close()
            self.assertTrue((Path(directory)/'sessions.sqlite3').exists())
