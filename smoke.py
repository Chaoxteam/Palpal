"""Opt-in packaged GUI check. Uses temporary data and no real student activity."""
import json
from pathlib import Path
import tempfile
from desktop import app as app_module


def run(report_path):
    report={'passed':False,'checks':{}}
    original_data=app_module.DATA
    original_error=app_module.messagebox.showerror
    app=None
    def error_dialog(*args,**kwargs): raise RuntimeError('Desktop initialization or save failed')
    try:
        with tempfile.TemporaryDirectory(prefix='palpal-smoke-') as directory:
            app_module.DATA=Path(directory)
            app_module.messagebox.showerror=error_dialog
            app=app_module.App()
            def checks():
                try:
                    if app.server is None: raise RuntimeError('Local bridge unavailable')
                    report['checks']['assets_loaded']=bool(app.canvas.winfo_exists())
                    report['checks']['foreground_hook']=bool(app.monitor.available)
                    if not report['checks']['foreground_hook']: raise RuntimeError('Foreground hook unavailable')
                    app.goal.delete(0,'end');app.goal.insert(0,'Study algebra')
                    app.start()
                    report['checks']['session_started']=app.session.state=='focus'
                    app.take_break()
                    report['checks']['break_disables_monitoring']=app.bridge_state() is None
                    app.stop(progress_note='Start at question 9')
                    report['checks']['summary_saved']=app.store.history()[0]['progress_note']=='Start at question 9'
                    report['passed']=all(report['checks'].values())
                except Exception as error:
                    report['error_type']=type(error).__name__
                finally:
                    app.close()
            app.root.after(1000,checks)
            app.root.mainloop()
    except Exception as error:
        report['error_type']=type(error).__name__
        if app:
            try: app.close()
            except Exception: pass
    finally:
        app_module.DATA=original_data
        app_module.messagebox.showerror=original_error
        Path(report_path).write_text(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1
