"""Shared deterministic file and configuration helpers."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def read_csv(path):
    return pd.read_csv(ROOT / path, encoding='utf-8-sig', keep_default_na=True)

def write_csv(frame, path):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False, encoding='utf-8-sig')

def load_config(name):
    return json.loads((ROOT / 'config' / name).read_text(encoding='utf-8'))

def write_json(value, path):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding='utf-8')

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
