import os
from datetime import datetime
from .config import cfg

LOG_PATH = cfg.get("global", "log_path")

def log(message):
    os.makedirs(LOG_PATH, exist_ok=True)
    filename = os.path.join(LOG_PATH, "merge.log")
    with open(filename, "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")
