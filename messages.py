"""Prewritten, age-specific messages. Return encouragement is optional."""
import json
from pathlib import Path

LIBRARY=json.loads((Path(__file__).resolve().parents[1]/'data/messages.json').read_text())
AGES=['6–9','10–12','13+']
class Messages:
    def __init__(self): self.previous={}; self.last_return=None
    def choose(self,event,age,now):
        if event=='return':
            if self.last_return is not None and now-self.last_return<180: return ''
            self.last_return=now
        options=LIBRARY[event][AGES.index(age)]
        previous=self.previous.get(event)
        choice=next((text for text in options if text!=previous),options[0])
        self.previous[event]=choice
        return choice
