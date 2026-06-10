import json
import hashlib
import datetime
from dataclasses import dataclass
from typing import Optional

VIOLATION_LOG_PATH = 'violations.jsonl'

@dataclass
class GuardResult:
    passed: bool
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    sanitized_text: Optional[str] = None

def _hash_input(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def log_violation(category: str, scanner_name: str, input_text: str):
    entry = {
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'category': category,
        'scanner_name': scanner_name,
        'input_hash': _hash_input(input_text)
    }
    with open(VIOLATION_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
