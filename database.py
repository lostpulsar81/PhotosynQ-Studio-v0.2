
import sqlite3
from pathlib import Path

DB_PATH = Path("photosynq_studio.db")

COLUMNS = [
    "imported_at", "source_file", "experiment", "treatment", "sample_id",
    "plant_id", "replicate", "notes", "timestamp", "phi2", "phinpq",
    "phino", "npqt", "ql", "lef", "spad", "ecst", "vhplus", "ghplus",
    "pmf", "p700", "ps1_active_centers", "ps1_open_centers",
    "ps1_oxidized_centers", "ps1_over_reduced_centers", "par",
    "leaf_temperature", "ambient_temperature", "humidity", "pressure",
    "thickness", "angle", "direction", "raw_json"
]

def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imported_at TEXT,
            source_file TEXT,
            experiment TEXT,
            treatment TEXT,
            sample_id TEXT,
            plant_id TEXT,
            replicate TEXT,
            notes TEXT,
            timestamp TEXT,
            phi2 REAL,
            phinpq REAL,
            phino REAL,
            npqt REAL,
            ql REAL,
            lef REAL,
            spad REAL,
            ecst REAL,
            vhplus REAL,
            ghplus REAL,
            pmf REAL,
            p700 REAL,
            ps1_active_centers REAL,
            ps1_open_centers REAL,
            ps1_oxidized_centers REAL,
            ps1_over_reduced_centers REAL,
            par REAL,
            leaf_temperature REAL,
            ambient_temperature REAL,
            humidity REAL,
            pressure REAL,
            thickness REAL,
            angle REAL,
            direction TEXT,
            raw_json TEXT
        )
    """)
    conn.commit()

def insert_measurements(conn, rows):
    count = 0
    placeholders = ",".join(["?"] * len(COLUMNS))
    for row in rows:
        values = [row.get(c) for c in COLUMNS]
        conn.execute(f"INSERT INTO measurements ({','.join(COLUMNS)}) VALUES ({placeholders})", values)
        count += 1
    conn.commit()
    return count

def fetch_measurements(conn):
    return conn.execute("SELECT * FROM measurements ORDER BY id DESC").fetchall()

def delete_all(conn):
    conn.execute("DELETE FROM measurements")
    conn.commit()
