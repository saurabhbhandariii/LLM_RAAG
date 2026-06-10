import asyncio
from typing import Tuple

try:
    from guardrails import Guard
    from guardrails.validators import ToxicLanguage, DetectPII, RestrictToTopic
except Exception:
    Guard = None
    ToxicLanguage = DetectPII = RestrictToTopic = None

from .base import GuardResult, log_violation


class GuardrailsLayer:

    def __init__(self, fallback_msg: str = "Sorry, I can't answer that heheehuhuh."):
        self.fallback_msg = fallback_msg
        if Guard:
            self.guard = Guard(
                validators=[
                    ToxicLanguage(),
                    DetectPII(),
                    RestrictToTopic(topics=["violence", "weapons", "politics"]),
                ]
            )
        else:
            self.guard = None

    def _run_guard(self, text: str) -> Tuple[bool, str]:

        if not self.guard:
            return True, ""
        try:
            result = self.guard.validate(text)
            passed = result.get("passed", True)
            reason = result.get("reason", "")
            return passed, reason
        except Exception:
            return True, ""

    async def validate(self, response: str) -> GuardResult:
        is_valid, reason = self._run_guard(response)
        if not is_valid:
            log_violation(
                category=reason or "Guardrails",
                scanner_name="Guardrails",
                input_text=response,
            )
            return GuardResult(
                passed=False,
                blocked_by="Guardrails",
                reason=reason,
                sanitized_text=self.fallback_msg,
            )
        return GuardResult(passed=True, sanitized_text=response)
