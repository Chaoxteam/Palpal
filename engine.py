"""Pure session rules. Browser context is held only for the current session."""
from dataclasses import dataclass
import math
from core.classifier import classify, words, matches, STUDY, DISTRACTION, UNSURE

@dataclass
class Config:
    grace: float=20
    min_interval: float=90
    max_prompts: int=4
    repeated_window: float=600

class Session:
    def __init__(self, goal, minutes, now, config=None):
        if not isinstance(goal,str) or not goal.strip() or len(goal)>500: raise ValueError('Enter a goal of 1–500 characters.')
        if isinstance(minutes,bool) or not isinstance(minutes,(int,float)) or not math.isfinite(minutes) or not 1<=minutes<=240: raise ValueError('Focus duration must be 1–240 minutes.')
        self.goal=goal; self.duration=minutes*60; self.start=now
        self.config=config or Config(); self.approved=set()
        self.context=None; self.pending=None; self.last_prompt=None; self.prompts=0
        self.state='focus'; self.break_until=None; self.break_started=None; self.break_seconds=0
        self.redirects=0; self.last_kind=None; self.prompt_times=[]
        self.break_reminded=False
    def observe(self,title,domain,now):
        if self.state!='focus': return
        context=(domain,title)
        if context==self.context: return
        self.context=context
        kind=classify(self.goal,title,domain,self.approved)
        self.last_kind=kind
        self.pending=None if kind==STUDY else now
    def tick(self,now):
        if self.state=='break':
            if now>=self.break_until:
                self.state='ready'; self.pending=None; self.context=None
                return 'resume'
            if not self.break_reminded and self.break_until-now<=30:
                self.break_reminded=True; return 'break_ending'
            return None
        if self.state!='focus': return None
        if now-self.start-self.break_seconds>=self.duration:
            self.state='completed'; self.pending=None; return 'complete'
        if self.pending is None or now-self.pending<self.config.grace: return None
        if self.prompts>=self.config.max_prompts: return None
        if self.last_prompt is not None and now-self.last_prompt<self.config.min_interval: return None
        self.pending=None; self.last_prompt=now; self.prompts+=1
        self.prompt_times=[t for t in self.prompt_times if now-t<=self.config.repeated_window]
        self.prompt_times.append(now)
        return 'reset' if len(self.prompt_times)>=3 else 'check'
    def answer(self,answer,now):
        if self.state!='focus': return
        if answer=='study' and self.context:
            if len(self.approved)>=128: self.approved.pop()
            self.approved.add(self.context)
        if answer=='no': self.redirects+=1
        if answer=='break': self.start_break(now)
        self.pending=None
    def start_break(self,now):
        if self.state!='focus': return
        self.state='break'; self.break_started=now; self.break_until=now+300; self.pending=None; self.context=None
        self.break_reminded=False

    def resume(self,now):
        if self.state!='ready': return
        self.break_seconds+=now-self.break_started
        self.state='focus'; self.context=None; self.pending=None
    def elapsed(self,now):
        if hasattr(self,'final_elapsed'): return self.final_elapsed
        breaks=self.break_seconds+(now-self.break_started if self.state in ('break','ready') else 0)
        focus=max(0,now-self.start-breaks)
        if self.state=='completed': focus=min(focus,self.duration)
        return focus,breaks
