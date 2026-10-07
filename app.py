import queue, secrets, time, os
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from core.engine import Session, Config
from desktop.bridge import start_bridge
from desktop.windows_activity import foreground, start_monitor, BROWSERS
from core.storage import Store
from core.settings import load_settings, save_settings, DEFAULTS
from core.messages import Messages, AGES

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))/'PalPal'


class App:
    def __init__(self):
        DATA.mkdir(parents=True,exist_ok=True)
        path=DATA/'settings.json'
        try: self.settings=load_settings(path)
        except ValueError as error:
            messagebox.showerror('PalPal settings',str(error)); raise SystemExit(1)
        self.events=queue.Queue(maxsize=64); self.session=None
        self.epoch=None; self.last_browser_stamp=0; self.messages=Messages(); self.prompt_context=None; self.store=Store(DATA/"sessions.sqlite3")
        self.root=tk.Tk(); self.root.title('PalPal — Your study buddy'); self.root.geometry('480x570')
        self.root.configure(bg='#eef5fc')
        ttk.Label(self.root,text='PalPal',font=('Segoe UI',26,'bold')).pack(pady=12)
        ttk.Label(self.root,text='What are you working on?').pack()
        self.goal=ttk.Entry(self.root,width=42); self.goal.pack(pady=8); self.goal.insert(0,self.store.latest() or 'Study algebra')
        ttk.Label(self.root,text='How long do you want to focus? (minutes)').pack()
        self.minutes=tk.StringVar(value='25'); ttk.Combobox(self.root,textvariable=self.minutes,values=['15','25','45','60'],width=12).pack(pady=8)
        self.age=tk.StringVar(value='13+'); ttk.Combobox(self.root,textvariable=self.age,values=AGES,state='readonly',width=12).pack()
        ttk.Button(self.root,text='Start Focus',command=self.start).pack(pady=12)
        self.status=ttk.Label(self.root,text='Ready when you are.'); self.status.pack(pady=8)
        ttk.Button(self.root,text='5-minute break',command=self.take_break).pack()
        ttk.Button(self.root,text='Stop and save',command=self.finish).pack(pady=6)
        ttk.Button(self.root,text='Browser pairing token',command=self.pair).pack()
        ttk.Button(self.root,text='Settings',command=self.show_settings).pack(pady=3)
        ttk.Button(self.root,text='Session history',command=self.show_history).pack(pady=3)
        self.cat=tk.Toplevel(self.root); self.cat.overrideredirect(True); self.cat.attributes('-topmost',True)
        self.cat.geometry(f'220x245+{self.root.winfo_screenwidth()-250}+{self.root.winfo_screenheight()-320}')
        self.bubble=ttk.Label(self.cat,text='Ready to study?',wraplength=210); self.bubble.pack(pady=5)
        # Viewport onto the approved sheet: no recreated or altered character asset.
        self.sheet=ImageTk.PhotoImage(Image.open(ROOT/'assets/palpal-cat/approved-sheet.jpg'))
        self.canvas=tk.Canvas(self.cat,width=190,height=165,highlightthickness=0)
        self.canvas.pack(); self.cat_image=self.canvas.create_image(-15,-415,image=self.sheet,anchor='nw')
        self.buttons=ttk.Frame(self.cat); self.buttons.pack()
        self.canvas.bind('<Button-1>',lambda e:setattr(self,'drag',(e.x,e.y)))
        self.canvas.bind('<B1-Motion>',self.drag_cat)
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        try: self.server=start_bridge(self.settings['token'],self.events,self.bridge_state)
        except OSError:
            messagebox.showerror('PalPal','Local browser bridge unavailable. Close any other PalPal instance.'); self.server=None
        self.monitor=start_monitor(self.events,lambda:bool(self.bridge_state()))
        self.poll()
    def drag_cat(self,event):
        x=max(0,min(event.x_root-self.drag[0],self.root.winfo_screenwidth()-220))
        y=max(0,min(event.y_root-self.drag[1],self.root.winfo_screenheight()-245))
        self.cat.geometry(f'+{x}+{y}')
    def bridge_state(self):
        session=self.session
        return self.epoch if session and session.state=='focus' else None
    def pair(self):
        dialog=tk.Toplevel(self.root); dialog.title('Local browser pairing')
        ttk.Label(dialog,text='Paste this token into the extension options.').pack(padx=12,pady=12)
        entry=ttk.Entry(dialog,width=55); entry.insert(0,self.settings['token']); entry.pack(padx=12,pady=12)
    def start(self):
        if self.session: return
        try:
            minutes=float(self.minutes.get())
            if not 1<=minutes<=240 or not self.goal.get().strip() or len(self.goal.get().strip())>500: raise ValueError()
        except ValueError:
            messagebox.showinfo('Session','Enter a goal of up to 500 characters and 1–240 minutes.'); return
        self.session=Session(self.goal.get().strip(),minutes,time.monotonic(),Config(self.settings['grace'],self.settings['min_interval'],self.settings['max_prompts'],self.settings['repeated_window']))
        self.epoch=secrets.token_urlsafe(16); self.last_browser_stamp=0
        self.started=time.time(); self.session_age=self.age.get(); self.messages=Messages()
        self.say(self.message('start')); self.clear_buttons()
    def message(self,event):
        return self.messages.choose(event,getattr(self,'session_age',self.age.get()),time.monotonic())
    def avatar(self,state):
        # Switch original-sheet viewports, preserving the supplied character art.
        x={'idle':15,'talking':230,'thinking':445,'encouraging':645,'break':860,'completed':1070,'sleeping':860}.get(state,15)
        job=getattr(self,'avatar_job',None)
        if job: self.root.after_cancel(job)
        self.canvas.coords(self.cat_image,-x,-415)
        self.avatar_job=None
        if state=='idle' and self.session and self.session.state=='focus':
            def breathe(up=False):
                self.canvas.coords(self.cat_image,-x,-416 if up else -415)
                self.avatar_job=self.root.after(350 if up else 3000,lambda:breathe(not up))
            self.avatar_job=self.root.after(3000,lambda:breathe(True))
    def say(self,text):
        job=getattr(self,'bubble_job',None)
        if job: self.root.after_cancel(job)
        self.bubble_job=None
        self.bubble.config(text=text)
        self.avatar('break' if self.session and self.session.state=='break' else 'sleeping' if not self.session else 'talking' if text else 'idle')
        if text:
            def quiet():
                if self.prompt_context is None: self.say('')
            self.bubble_job=self.root.after(6000,quiet)
    def clear_buttons(self):
        self.prompt_context=None
        for child in self.buttons.winfo_children(): child.destroy()
    def answer(self,value):
        if not self.session: return
        if self.prompt_context is not None and self.prompt_context!=self.session.context:
            self.clear_buttons(); return
        self.session.answer(value,time.monotonic()); self.clear_buttons()
        if value=='break':
            self.epoch=secrets.token_urlsafe(16); self.last_browser_stamp=0
        self.say('Back to '+self.session.goal+'.' if value=='no' else self.message('break') if value=='break' else '')
    def take_break(self):
        if self.session and self.session.state=='focus': self.answer('break')
    def poll(self):
        now=time.monotonic()
        for _ in range(64):
            try: context=self.events.get_nowait()
            except queue.Empty: break
            if self.session and self.session.state=='focus':
                if context['source']=='window':
                    app=context['app']
                    current=foreground()
                    if current is not None and app!=current: continue
                    if app=='palpal': continue
                    self.session.context=None; self.session.pending=None
                    self.clear_buttons(); self.say('')
                    if app in BROWSERS or not app: continue
                    title,domain=app,''
                else:
                    app=foreground()
                    if context['epoch']!=self.epoch or context['timestamp']<=self.last_browser_stamp or time.time()*1000-context['timestamp']>5000: continue
                    if app is not None and app!=context['browser']: continue
                    self.last_browser_stamp=context['timestamp']
                    title,domain=context['title'],context['domain']
                    if not domain:
                        self.session.context=None; self.session.pending=None; self.clear_buttons(); self.say(''); continue
                previous=self.session.last_kind
                changed=self.session.context!=(domain,title)
                self.session.observe(title,domain,now)
                if changed: self.clear_buttons(); self.say('')
                if self.session.last_kind=='STUDY' and previous in ('DISTRACTION','UNSURE'):
                    self.say(self.message('return'))
        if self.session and self.session.state!='saving':
            # Verify foreground only before a possible intervention, not on every timer tick.
            if self.session.pending is not None and now-self.session.pending>=self.session.config.grace:
                app=foreground()
                domain,title=self.session.context or ('','')
                valid=app is None or app=='palpal' or (app in BROWSERS if domain else app==title)
                if not valid:
                    self.session.pending=None; self.session.context=None; self.clear_buttons()
            event=self.session.tick(now)
            if event in ('check','reset'):
                self.say(self.message(event)); self.clear_buttons(); self.prompt_context=self.session.context
                options=[("Yes, study",'study'),('No','no'),('Break','break')] if event=='check' else [('Keep going','continue'),('5-min break','break')]
                for label,value in options: ttk.Button(self.buttons,text=label,command=lambda v=value:self.answer(v)).pack(side='left')
            elif event=='resume':
                self.epoch=secrets.token_urlsafe(16); self.last_browser_stamp=0
                self.say(self.message('resume')); self.clear_buttons()
                ttk.Button(self.buttons,text='Continue',command=self.resume).pack()
            elif event=='break_ending': self.say(self.message('break_ending'))
            elif event=='complete':
                self.say(self.message('block')); self.finish(completed=True)
            if self.session:
                left=self.session.break_until-now if self.session.state=='break' else 0 if self.session.state=='ready' else self.session.duration-self.session.elapsed(now)[0]
                self.status.config(text=f'{self.session.state.title()} — {max(0,int(left))//60:02}:{max(0,int(left))%60:02}')
        self.root.after(500 if self.session else 5000,self.poll)
    def stop(self,completed=False,goal_completed=False,progress_note=''):
        if not self.session: return
        s=self.session; now=time.monotonic()
        focus,breaks=s.elapsed(now)
        record={'goal':s.goal,'start':self.started,'end':time.time(),'planned_seconds':s.duration,'focus_seconds':focus,'break_seconds':breaks,'redirects':s.redirects,'block_completed':completed,'goal_completed':goal_completed,'progress_note':progress_note}
        # Session summaries only; titles/domains never written.
        try: self.store.save(record)
        except (OSError,sqlite3.DatabaseError):
            messagebox.showerror('Save unavailable','Your session is still here. Free disk space or restore access, then try saving again.')
            return False
        self.session=None; self.epoch=None; self.clear_buttons(); self.status.config(text='Session saved.')
        self.say(self.message('complete' if goal_completed else 'saved'))
        if goal_completed: self.avatar('completed')
        return True
    def resume(self):
        if not self.session or self.session.state!='ready': return
        self.session.resume(time.monotonic())
        self.epoch=secrets.token_urlsafe(16); self.last_browser_stamp=0
        self.clear_buttons(); self.say('')
    def finish(self,completed=False):
        if not self.session or self.session.state=='saving': return
        # Stop monitoring while the student records their progress.
        session=self.session
        self.epoch=None
        session.final_elapsed=session.elapsed(time.monotonic()); session.state='saving'
        dialog=tk.Toplevel(self.root); dialog.title('Save your progress'); dialog.grab_set()
        ttk.Label(dialog,text='What would help you pick this up next time?').pack(padx=16,pady=12)
        note=ttk.Entry(dialog,width=48); note.pack(padx=16,pady=8)
        done=tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog,text='I finished my goal',variable=done).pack(pady=8)
        ttk.Label(dialog,text='For example: 8 of 12 questions; start at question 9.').pack(padx=12,pady=8)
        def save():
            if self.session is session:
                if not self.stop(completed,done.get(),note.get().strip()[:500]): return
            dialog.destroy()
            if completed:
                self.clear_buttons()
                ttk.Button(self.buttons,text='5-minute reset',command=self.scheduled_break).pack()
        ttk.Button(dialog,text='Save session',command=save).pack(pady=12)
        dialog.protocol('WM_DELETE_WINDOW',save)
    def scheduled_break(self):
        if self.session: return
        self.minutes.set('10'); self.start(); self.take_break()
    def show_settings(self):
        dialog=tk.Toplevel(self.root); dialog.title('PalPal settings')
        labels={'grace':'Grace period (seconds)','min_interval':'Time between prompts (seconds)','max_prompts':'Maximum prompts per block','repeated_window':'Reset suggestion window (seconds)'}
        entries={}
        for name in DEFAULTS:
            ttk.Label(dialog,text=labels[name]).pack(padx=12,pady=4)
            entry=ttk.Entry(dialog); entry.insert(0,str(self.settings[name])); entry.pack(padx=12); entries[name]=entry
        ttk.Label(dialog,text='Changes apply to the next focus session.').pack(padx=12,pady=8)
        def save():
            try:
                values=dict(self.settings)
                for name,entry in entries.items(): values[name]=int(entry.get()) if name=='max_prompts' else float(entry.get())
                self.settings=save_settings(DATA/'settings.json',values)
            except (ValueError,OSError) as error:
                messagebox.showinfo('Settings',str(error),parent=dialog); return
            dialog.destroy()
        ttk.Button(dialog,text='Save settings',command=save).pack(pady=12)
    def show_history(self):
        dialog=tk.Toplevel(self.root); dialog.title('Your study progress'); dialog.geometry('720x420')
        ttk.Label(dialog,text='Only goals and session summaries are saved.').pack(pady=8)
        tree=ttk.Treeview(dialog,columns=('goal','minutes','done','note'),show='headings')
        for name,label in [('goal','Goal'),('minutes','Focus minutes'),('done','Goal complete'),('note','Next step')]:
            tree.heading(name,text=label); tree.column(name,width=170)
        tree.pack(fill='both',expand=True,padx=8)
        rows=self.store.history()
        for row in rows: tree.insert('', 'end',iid=row['id'],values=(row['goal'],round(row['focus_seconds']/60,1),'Yes' if row['goal_completed'] else '',row['progress_note']))
        def use_goal():
            selected=tree.selection()
            if selected:
                row=next(row for row in rows if row['id']==selected[0])
                self.goal.delete(0,'end'); self.goal.insert(0,row['goal']); dialog.destroy()
        def delete():
            if messagebox.askyesno('Delete saved summaries','Delete all locally saved session summaries?',parent=dialog):
                self.store.delete_all()
                legacy=DATA/'sessions.jsonl'
                if legacy.exists(): legacy.unlink()
                rows.clear()
                for item in tree.get_children(): tree.delete(item)
        ttk.Button(dialog,text='Use selected goal',command=use_goal).pack(side='left',padx=12,pady=8)
        ttk.Button(dialog,text='Delete all summaries',command=delete).pack(side='right',padx=12,pady=8)
    def close(self):
        if self.session and not self.stop(): return
        if self.server:
            self.server.shutdown(); self.server.server_close()
        if getattr(self,'monitor',None): self.monitor.stop()
        self.store.close()
        self.root.destroy()
    def run(self): self.root.mainloop()

if __name__=='__main__': App().run()
