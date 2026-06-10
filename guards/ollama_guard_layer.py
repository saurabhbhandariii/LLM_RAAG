import asyncio
import json
from typing import Tuple

try:
    from ollama_guard import Guard as OllamaGuard
except Exception:
    OllamaGuard = None

from .base import GuardResult, log_violation


class OllamaGuardLayer:

    def __init__(self):
        if OllamaGuard:
            try:
                self.guard = OllamaGuard()
            except Exception:
                self.guard = None
        else:
            self.guard = None

    async def _run_guard(self, text: str) -> Tuple[bool, str]:

        loop = asyncio.get_event_loop()

        def _call():
            if not self.guard:
                return True, ""
            try:
                result = self.guard.check(text)
                unsafe = result.get("unsafe", False)
                category = result.get("category", "")
                return not unsafe, category
            except Exception as e:
                return True, ""

        return await loop.run_in_executor(None, _call)

    async def scan_input(self, prompt: str) -> GuardResult:
        is_safe, category = await self._run_guard(prompt)
        if not is_safe:
            log_violation(
                category=category or "OllamaGuard",
                scanner_name="OllamaGuard",
                input_text=prompt,
            )
            return GuardResult(
                passed=False,
                blocked_by="OllamaGuard",
                reason=category,
                sanitized_text=None,
            )
        return GuardResult(passed=True, sanitized_text=prompt)
