import re

_EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
_PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})")
_APIKEY_REGEX = re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([A-Za-z0-9\-_.]+)")
_PASSWORD_REGEX = re.compile(r"(?i)(password\s*[:=]\s*)([^\s]+)")


def sanitize_text(text: str) -> str:

    def _mask_phone(match: re.Match) -> str:
        number = match.group(0)
        digits = re.sub(r"\D", "", number)
        if len(digits) <= 4:
            return "[REDACTED_PHONE]"
        masked = "*" * (len(digits) - 4) + digits[-4:]
        prefix = ""
        if number.startswith("+"):
            prefix = "+"
        return f"{prefix}{masked}"

    def _mask_email(match: re.Match) -> str:
        email = match.group(0)
        parts = email.split("@")
        if len(parts) != 2:
            return "[REDACTED_EMAIL]"
        user = parts[0]
        domain = parts[1]
        masked_user = user[0] + "***" if len(user) > 1 else "*"
        return f"{masked_user}@{domain}"

    text = _EMAIL_REGEX.sub(_mask_email, text)
    text = _PHONE_REGEX.sub(_mask_phone, text)
    text = _APIKEY_REGEX.sub(r"\1[REDACTED]", text)
    text = _PASSWORD_REGEX.sub(r"\1[REDACTED]", text)
    return text
