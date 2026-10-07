"""Windows foreground events. Reads executable names, never window text."""
import ctypes
from ctypes import wintypes
import os
import queue
from threading import Thread, Event

BROWSERS={'chrome.exe','msedge.exe'}
if os.name=='nt':
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.GetCurrentThreadId.restype=wintypes.DWORD
    user.PostThreadMessageW.argtypes=[wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    user.UnhookWinEvent.argtypes=[wintypes.HANDLE]
    user.GetMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
    user.PeekMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT,wintypes.UINT]
    user.TranslateMessage.argtypes=[ctypes.POINTER(wintypes.MSG)]
    user.DispatchMessageW.argtypes=[ctypes.POINTER(wintypes.MSG)]
    user.DispatchMessageW.restype=ctypes.c_ssize_t

def foreground():
    if os.name!='nt': return None
    pid=wintypes.DWORD()
    user.GetWindowThreadProcessId(user.GetForegroundWindow(),ctypes.byref(pid))
    if pid.value==os.getpid(): return 'palpal'
    handle=kernel.OpenProcess(0x1000,False,pid.value)
    if not handle: return ''
    try:
        size=wintypes.DWORD(32768); buf=ctypes.create_unicode_buffer(size.value)
        if kernel.QueryFullProcessImageNameW(handle,0,buf,ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
        return ''
    finally: kernel.CloseHandle(handle)

class Monitor:
    def __init__(self):
        self.stopped=Event(); self.thread_id=None; self.available=None; self.thread=None
    def stop(self):
        self.stopped.set()
        if os.name=='nt' and self.thread_id:
            user.PostThreadMessageW(self.thread_id,0x12,0,0)  # WM_QUIT
        if self.thread: self.thread.join(timeout=1)

def start_monitor(events,enabled=lambda:True):
    monitor=Monitor()
    if os.name!='nt':
        monitor.available=False; return monitor
    def run():
        monitor.thread_id=kernel.GetCurrentThreadId()
        msg=wintypes.MSG()
        user.PeekMessageW(ctypes.byref(msg),None,0,0,0)  # Create thread message queue.
        callback_type=ctypes.WINFUNCTYPE(None,wintypes.HANDLE,wintypes.DWORD,wintypes.HWND,wintypes.LONG,wintypes.LONG,wintypes.DWORD,wintypes.DWORD)
        def changed(*args):
            if monitor.stopped.is_set() or not enabled(): return
            try: events.put_nowait({'source':'window','app':foreground()})
            except queue.Full: pass
        callback=callback_type(changed)
        user.SetWinEventHook.argtypes=[wintypes.DWORD,wintypes.DWORD,wintypes.HMODULE,callback_type,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD]
        user.SetWinEventHook.restype=wintypes.HANDLE
        hook=user.SetWinEventHook(3,3,None,callback,0,0,0)
        monitor.available=bool(hook)
        if not hook: return
        try:
            changed()
            while not monitor.stopped.is_set() and user.GetMessageW(ctypes.byref(msg),None,0,0)>0:
                user.TranslateMessage(ctypes.byref(msg)); user.DispatchMessageW(ctypes.byref(msg))
        finally: user.UnhookWinEvent(hook)
    monitor.thread=Thread(target=run,daemon=True)
    monitor.thread.start()
    return monitor
