"""Small deterministic classifier. Ambiguous overlap remains UNSURE."""
import json
import re
import unicodedata
from pathlib import Path

STUDY, DISTRACTION, UNSURE='STUDY','DISTRACTION','UNSURE'
RULES=json.loads((Path(__file__).resolve().parents[1]/'data/classification-rules.json').read_text())
STOP=set(RULES['stop_words'])

def words(text):
    normalized=unicodedata.normalize('NFKD',text.casefold())
    tokens=re.findall(r'[a-z0-9]+',normalized)
    # Conservative plural normalization; avoid damaging words such as physics.
    plurals={'equations':'equation','polynomials':'polynomial','triangles':'triangle','angles':'angle','cells':'cell','atoms':'atom','molecules':'molecule','forces':'force','reactions':'reaction'}
    return {plurals.get(token,token) for token in tokens if token not in STOP}

def matches(domain,known):
    return any(domain==d or domain.endswith('.'+d) for d in known)

def classify(goal,title,domain,approved=()):
    domain=domain.casefold().rstrip('.')
    if (domain,title) in approved: return STUDY
    goal_words,title_words=words(goal),words(title)
    overlap=goal_words & title_words
    subject_match=any(goal_words & set(group) and title_words & set(group) for group in RULES['subjects'].values())
    entertainment=title_words & set(RULES['entertainment_words'])
    # A relevant educational topic mixed with entertainment signals is ambiguous.
    if overlap or subject_match:
        if entertainment-goal_words: return UNSURE
        return STUDY
    if not domain:
        app=title.casefold()
        if app in RULES['study_apps']: return STUDY
        if app in RULES['distraction_apps']: return DISTRACTION
        return UNSURE
    if matches(domain,RULES['study_domains']): return STUDY
    if matches(domain,['youtube.com','youtu.be']):
        return DISTRACTION if entertainment else UNSURE
    if matches(domain,RULES['distraction_domains']): return DISTRACTION
    return UNSURE
