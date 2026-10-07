"""SQLite stores summaries only; schema cannot accept browser activity."""
import sqlite3
import uuid

class Store:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, goal TEXT NOT NULL, start REAL, end REAL, planned_seconds REAL, focus_seconds REAL, break_seconds REAL, redirects INTEGER, block_completed INTEGER)")
        names={row[1] for row in self.db.execute('PRAGMA table_info(sessions)')}
        for name,kind in [('goal_completed','INTEGER DEFAULT 0'),('progress_note',"TEXT DEFAULT ''")]:
            if name not in names: self.db.execute(f'ALTER TABLE sessions ADD COLUMN {name} {kind}')
        self.db.commit()
    def save(self,record):
        record=dict(record,goal_completed=record.get('goal_completed',False),progress_note=record.get('progress_note',''))
        columns=('goal','start','end','planned_seconds','focus_seconds','break_seconds','redirects','block_completed','goal_completed','progress_note')
        with self.db:
            self.db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),*(record[k] for k in columns)))
    def latest(self):
        row=self.db.execute('SELECT goal FROM sessions ORDER BY end DESC LIMIT 1').fetchone()
        return row[0] if row else None
    def history(self):
        self.db.row_factory=sqlite3.Row
        return [dict(row) for row in self.db.execute('SELECT * FROM sessions ORDER BY end DESC LIMIT 100')]
    def delete_all(self):
        with self.db: self.db.execute('DELETE FROM sessions')
        self.db.execute('VACUUM')
    def close(self): self.db.close()
