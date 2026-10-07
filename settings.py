"""Validate local settings without changing existing pairing credentials."""
import json
import math
import secrets

DEFAULTS={'grace':20,'min_interval':90,'max_prompts':4,'repeated_window':600}
def validate_settings(values):
    values=dict(values)
    token=values.get("token")
    if not isinstance(token,str) or not 20<=len(token)<=256 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("Invalid pairing token.")
    for name,default in DEFAULTS.items():
        value=values.get(name,default)
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value): raise ValueError(f"{name} must be finite.")
        if name=="max_prompts":
            if not isinstance(value,int) or not 0<=value<=20: raise ValueError("Prompt cap must be 0–20.")
        elif not 1<=value<=3600: raise ValueError(f"{name} must be 1–3600 seconds.")
        values[name]=value
    return values

def save_settings(path,values):
    values=validate_settings(values)
    temporary=path.with_suffix(".tmp")
    temporary.write_text(json.dumps(values))
    temporary.replace(path)
    return values

def load_settings(path):
    if path.exists():
        try: values=json.loads(path.read_text())
        except (ValueError,OSError) as error: raise ValueError('Settings could not be read. Restore a valid settings.json.') from error
        if not isinstance(values,dict): raise ValueError('Settings must be an object.')
    else: values={'token':secrets.token_urlsafe(32)}
    values=validate_settings(values)
    if not path.exists(): path.write_text(json.dumps(values))
    return values
