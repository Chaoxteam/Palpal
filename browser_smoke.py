"""Windows-only real MV3 extension/desktop test using synthetic, routed pages.
Requires playwright and its Chromium download. No study/browser data is uploaded.
"""
from contextlib import ExitStack
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

# Support direct execution from repository root.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def run(report_path):
    if os.name!='nt': raise RuntimeError('This smoke test needs Windows foreground APIs.')
    from playwright.sync_api import sync_playwright
    from desktop import app as app_module
    report={'passed':False,'checks':{}}
    app=None;context=None;worker=None
    original_data=app_module.DATA
    original_error=app_module.messagebox.showerror
    def no_dialog(*args,**kwargs): raise RuntimeError('Desktop initialization or saving failed')
    def remember_error(error,cleanup=False):
        description={'type':type(error).__name__,'message':str(error)[:1000]}
        if cleanup or 'error_type' in report:
            report.setdefault('cleanup_errors',[]).append(description)
        else:
            report['error_type']=description['type'];report['error']=description['message']
    def close_resource(close):
        try: close()
        except Exception as error: remember_error(error,cleanup=True)
    try:
        with ExitStack() as stack:
            directory=stack.enter_context(tempfile.TemporaryDirectory(prefix='palpal-browser-smoke-'))
            try:
                app_module.DATA=Path(directory)/'data'
                app_module.messagebox.showerror=no_dialog
                app=app_module.App()
                stack.callback(close_resource,app.close)
                # Map Tk windows before Chromium, so their first update cannot steal browser focus.
                app.root.update()
                app.settings.update(grace=1,min_interval=1)
                report['phase']='browser startup'
                playwright=stack.enter_context(sync_playwright())
                extension=Path(__file__).resolve().parents[1]/'extension'
                context=playwright.chromium.launch_persistent_context(
                    str(Path(directory)/'browser'),headless=False,channel='chromium',
                    ignore_default_args=['--disable-extensions'],
                    args=[f'--disable-extensions-except={extension}',f'--load-extension={extension}'])
                stack.callback(close_resource,context.close)
                worker=context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker')
                worker.evaluate('(token) => chrome.storage.local.set({token})',app.settings['token'])
                page=context.new_page()
                # Synthetic YouTube documents exercise classification without fetching the site.
                def document(route):
                    title='Quadratic equations explained' if 'study' in route.request.url else 'Funniest Minecraft Moments'
                    route.fulfill(status=200,content_type='text/html',body=f'<html><head><title>{title}</title></head><body>PalPal test page</body></html>')
                context.route('https://www.youtube.com/**',document)
                def wait_for(condition,label,seconds=15):
                    deadline=time.monotonic()+seconds
                    while time.monotonic()<deadline:
                        app.root.update()
                        if condition(): return
                        page.wait_for_timeout(50)
                    raise RuntimeError(label)
                report['phase']='study context'
                app.goal.delete(0,'end');app.goal.insert(0,'Study algebra');app.start()
                page.goto('https://www.youtube.com/study');page.bring_to_front()
                wait_for(lambda:app.session.last_kind=='STUDY','Study context never arrived')
                report['checks']['study_quiet']=app.session.prompts==0
                report['phase']='distraction prompt'
                page.goto('https://www.youtube.com/entertainment');page.bring_to_front()
                wait_for(lambda:app.session.prompts==1,'Distraction prompt never arrived')
                report['checks']['extension_to_desktop']=app.prompt_context is not None
                app.answer('no')
                report['checks']['redirect_recorded']=app.session.redirects==1
                page.goto('https://www.youtube.com/study-again');page.bring_to_front()
                wait_for(lambda:app.session.last_kind=='STUDY','Return context never arrived')
                report['checks']['return_cancels_prompt']=app.session.pending is None
                app.take_break()
                page.goto('https://www.youtube.com/entertainment-during-break');page.bring_to_front()
                page.wait_for_timeout(500);app.root.update()
                report['checks']['break_discards_context']=app.session.context is None and app.bridge_state() is None
                app.stop(progress_note='Resume at question 9')
                record=app.store.history()[0]
                report['checks']['summary_only']='title' not in record and 'domain' not in record
                report['passed']=all(report['checks'].values())
            except Exception as error:
                remember_error(error)
                if app and app.session:
                    report['diagnostics']={
                        'session_state':app.session.state,
                        'classification':app.session.last_kind,
                        'browser_event_received':bool(app.last_browser_stamp),
                        'foreground_hook':bool(app.monitor.available),
                        'foreground_app':app_module.foreground()}
                if worker:
                    try:
                        report['extension_diagnostics']=worker.evaluate('''async () => {
                            const {token}=await chrome.storage.local.get('token');
                            const windows=await chrome.windows.getAll();
                            const result={paired:Boolean(token),focused_browser_window:windows.some(w=>w.focused),
                                loopback_permission:await chrome.permissions.contains({origins:['http://127.0.0.1:47831/*']})};
                            try {
                                const response=await fetch('http://127.0.0.1:47831/status',{headers:{Authorization:'Bearer '+token}});
                                result.http_status=response.status;
                                if(response.ok) result.monitoring_enabled=Boolean((await response.json()).epoch);
                            } catch(error) { result.transport_error=String(error); }
                            return result;
                        }''')
                    except Exception as diagnostic_error:
                        report['extension_diagnostics']={'error':str(diagnostic_error)[:300]}
    except Exception as error:
        remember_error(error,cleanup='error_type' in report)
    finally:
        app_module.DATA=original_data
        app_module.messagebox.showerror=original_error
        if 'error_type' in report or report.get('cleanup_errors'): report['passed']=False
        output=Path(report_path);output.parent.mkdir(parents=True,exist_ok=True)
        encoded=json.dumps(report,indent=2)
        output.write_text(encoded)
        print(encoded)
    return 0 if report['passed'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',default='reports/browser-smoke.json')
    arguments=parser.parse_args()
    raise SystemExit(run(arguments.report))
