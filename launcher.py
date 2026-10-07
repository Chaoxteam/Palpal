"""PyInstaller entry point. Packaged smoke checks run only when explicitly requested."""
import sys
from desktop.app import App
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--smoke-report':
        from desktop.smoke import run
        raise SystemExit(run(sys.argv[2]))
    App().run()
