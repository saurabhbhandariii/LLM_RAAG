"""
Privacy & Security Configuration
Centralized settings for all guard layers and privacy mechanisms
"""

import os
from typing import Dict, List

# ============================================================================
# LLM GUARD CONFIGURATION
# ============================================================================

LLM_GUARD_CONFIG = {
    "enabled": True,
    "input_scanners": {
        "prompt_injection": {
            "enabled": True,
            "threshold": 0.3,  # Lowered from 0.5 for better detection
            "match_type": "FULL",  # Can be FULL, PARTIAL, SENTENCE
        },
        "toxicity": {
            "enabled": True,
            "threshold": 0.4,  # Lowered from 0.5 for better detection
            "language": "en",
        },
        "secrets": {
            "enabled": True,
            "redact": True,
            "patterns": [
                "api_key", "api_secret", "apikey", "apisecret",
                "password", "passwd", "pwd",
                "token", "access_token", "refresh_token", "auth_token",
                "secret", "client_secret", "consumer_secret",
                "aws_key", "aws_secret", "aws_access_key",
                "private_key", "private_rsa_key",
                "database_password", "db_password",
                "jwt", "bearer",
            ],
        },
        "anonymize": {
            "enabled": True,
            "pii_types": [
                "EMAIL", "PHONE", "IP_ADDRESS", "CREDIT_CARD", "SSN",
                "NAME", "PERSON", "LOCATION", "ORGANIZATION"
            ],
        },
        "language": {
            "enabled": True,
            "allowed_languages": ["en"],
        },
        "code_scanner": {
            "enabled": True,
            "languages": ["python", "javascript", "sql", "bash", "yaml", "json"],
        },
    },
    "output_scanners": {
        "toxicity": {
            "enabled": True,
            "threshold": 0.4,  # Lowered from 0.5 for better detection
        },
        "sensitive": {
            "enabled": True,
            "redact_pii": True,
        },
        "factuality": {
            "enabled": True,
            "check_sources": True,
        },
        "bias": {
            "enabled": True,
            "threshold": 0.4,  # Lowered from 0.5 for better detection
        },
    },
}

# ============================================================================
# LLAMA GUARD CONFIGURATION
# ============================================================================

LLAMA_GUARD_CONFIG = {
    "enabled": True,
    "model": "meta-llama/Llama-2-7b-chat-hf",  # or 13b for more accuracy
    "safety_categories": [
        "violence",
        "sexual",
        "harassment",
        "hate_speech",
        "illegal",
        "malware",
        "physical_harm",
        "economic_harm",
        "fraud",
        "deception",
        "privacy_violation",
    ],
    "threshold": 0.5,  # Confidence threshold for violations
}

# ============================================================================
# PII & SENSITIVE DATA PATTERNS
# ============================================================================

PII_PATTERNS = {
    "EMAIL": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
    "PHONE": r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})",
    "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "IP_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    "API_KEY": r"(?i)(api[_-]?key\s*[:=]\s*)([A-Za-z0-9\-_.]{20,})",
    "PASSWORD": r"(?i)(password\s*[:=]\s*)([^\s'\"]+)",
    "CREDIT_CARD_DETAILED": r"(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})",
    "AWS_KEY": r"(?i)(AKIA[0-9A-Z]{16}|aws_?(?:access_?)?key|aws_?secret)",
    "JWT_TOKEN": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "DATABASE_URL": r"(?i)(postgres|mysql|mongodb|sqlite)://[^\s]+",
    "BEARER_TOKEN": r"(?i)(bearer\s+[A-Za-z0-9\-._~+/]+=*)",
    "GITHUB_TOKEN": r"ghp_[0-9a-zA-Z]{36}",
    "PRIVATE_KEY": r"-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----",
    "AUTH_TOKEN": r"(?i)(auth[_-]?token|access[_-]?token|refresh[_-]?token|authorization)\s*[:=]\s*([A-Za-z0-9\-_.]+)",
    "SLACK_TOKEN": r"(?i)xox[pab]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]+",
    "STRIPE_KEY": r"(?i)(sk|pk)_(?:live|test)_[0-9a-zA-Z]{20,}",
}

# ============================================================================
# REDACTION RULES
# ============================================================================

REDACTION_RULES = {
    "emails": {
        "pattern": PII_PATTERNS["EMAIL"],
        "replacement": "[REDACTED_EMAIL]",
        "partial_mask": True,
    },
    "phones": {
        "pattern": PII_PATTERNS["PHONE"],
        "replacement": "[REDACTED_PHONE]",
        "partial_mask": True,
    },
    "credit_cards": {
        "pattern": PII_PATTERNS["CREDIT_CARD"],
        "replacement": "[REDACTED_CARD]",
        "partial_mask": False,
    },
    "ssn": {
        "pattern": PII_PATTERNS["SSN"],
        "replacement": "[REDACTED_SSN]",
        "partial_mask": False,
    },
    "api_keys": {
        "pattern": PII_PATTERNS["API_KEY"],
        "replacement": r"\1[REDACTED]",
        "partial_mask": False,
    },
    "passwords": {
        "pattern": PII_PATTERNS["PASSWORD"],
        "replacement": r"\1[REDACTED]",
        "partial_mask": False,
    },
    "aws_keys": {
        "pattern": PII_PATTERNS["AWS_KEY"],
        "replacement": "[REDACTED_AWS_KEY]",
        "partial_mask": False,
    },
    "jwt_tokens": {
        "pattern": PII_PATTERNS["JWT_TOKEN"],
        "replacement": "[REDACTED_JWT]",
        "partial_mask": False,
    },
    "database_urls": {
        "pattern": PII_PATTERNS["DATABASE_URL"],
        "replacement": "[REDACTED_DB_URL]",
        "partial_mask": False,
    },
    "bearer_tokens": {
        "pattern": PII_PATTERNS["BEARER_TOKEN"],
        "replacement": "[REDACTED_TOKEN]",
        "partial_mask": False,
    },
    "auth_tokens": {
        "pattern": PII_PATTERNS["AUTH_TOKEN"],
        "replacement": r"\1=[REDACTED]",
        "partial_mask": False,
    },
    "github_tokens": {
        "pattern": PII_PATTERNS["GITHUB_TOKEN"],
        "replacement": "[REDACTED_GITHUB_TOKEN]",
        "partial_mask": False,
    },
    "stripe_keys": {
        "pattern": PII_PATTERNS["STRIPE_KEY"],
        "replacement": "[REDACTED_STRIPE_KEY]",
        "partial_mask": False,
    },
    "private_keys": {
        "pattern": PII_PATTERNS["PRIVATE_KEY"],
        "replacement": "[REDACTED_PRIVATE_KEY]",
        "partial_mask": False,
    },
    "slack_tokens": {
        "pattern": PII_PATTERNS["SLACK_TOKEN"],
        "replacement": "[REDACTED_SLACK_TOKEN]",
        "partial_mask": False,
    },
}

# ============================================================================
# VIOLATION LOGGING CONFIG
# ============================================================================

VIOLATION_CONFIG = {
    "log_file": "violations.jsonl",
    "include_timestamp": True,
    "hash_inputs": True,  # Hash sensitive inputs before logging
    "hash_algorithm": "sha256",
    "log_categories": [
        "prompt_injection",
        "toxicity",
        "pii_detected",
        "secrets_detected",
        "illegal_content",
        "privacy_violation",
    ],
}

# ============================================================================
# PRIVACY LEVELS
# ============================================================================

PRIVACY_LEVELS = {
    "STRICT": {
        "sanitize_pii": True,
        "anonymize_identities": True,
        "redact_sensitive": True,
        "check_toxic": True,
        "check_secrets": True,
        "llama_guard_enabled": True,
        "audit_all_requests": True,
    },
    "STANDARD": {
        "sanitize_pii": True,
        "anonymize_identities": False,
        "redact_sensitive": True,
        "check_toxic": True,
        "check_secrets": True,
        "llama_guard_enabled": True,
        "audit_all_requests": False,
    },
    "BASIC": {
        "sanitize_pii": True,
        "anonymize_identities": False,
        "redact_sensitive": False,
        "check_toxic": False,
        "check_secrets": True,
        "llama_guard_enabled": False,
        "audit_all_requests": False,
    },
}

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_CONFIG = {
    "groq": {
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 1,
        "models": [
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "mixtral-8b-32768",
        ],
    },
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llama2"),
        "timeout": 60,
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_privacy_level() -> str:
    """Get configured privacy level from environment or default to STANDARD"""
    return os.getenv("PRIVACY_LEVEL", "STANDARD").upper()


def get_privacy_config() -> Dict:
    """Get privacy configuration based on privacy level"""
    level = get_privacy_level()
    return PRIVACY_LEVELS.get(level, PRIVACY_LEVELS["STANDARD"])


def is_strict_mode() -> bool:
    """Check if running in strict privacy mode"""
    return get_privacy_level() == "STRICT"
