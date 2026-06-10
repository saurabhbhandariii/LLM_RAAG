import asyncio
from typing import Tuple

# Attempt to import llm_guard scanners; fallback to None
try:
    from llm_guard.vault import Vault
    from llm_guard.input_scanners import PromptInjection, BanTopics, Toxicity, Secrets, Anonymize, BanSubstrings
    from llm_guard.input_scanners.anonymize import DEFAULT_ENTITY_TYPES
    from llm_guard.output_scanners import Toxicity as OutputToxicity, Sensitive, BanTopics as OutputBanTopics
except Exception as e:
    import logging
    logging.warning(f"Failed to import llm_guard scanners: {e}")
    Vault = PromptInjection = BanTopics = Toxicity = Secrets = Anonymize = BanSubstrings = None
    DEFAULT_ENTITY_TYPES = []
    OutputToxicity = Sensitive = OutputBanTopics = None

from .base import GuardResult, log_violation

class LLMGuardLayer:
    """Wrapper for llm‑guard input and output scanners.

    All methods are async to fit the overall pipeline but the underlying
    scanners are synchronous, so they are executed in a thread pool.
    """

    def __init__(self):
        # Initialize scanners if available
        self.input_scanners = []
        if PromptInjection:
            self.input_scanners.append(('PromptInjection', PromptInjection(threshold=0.5)))
        if BanTopics:
            self.input_scanners.append(('BanTopics', BanTopics(topics=["violence", "weapons"])))
        if Toxicity:
            self.input_scanners.append(('Toxicity', Toxicity(threshold=0.5)))
        if Anonymize and Vault:
            vault = Vault()
            self.input_scanners.append(('Anonymize', Anonymize(vault)))
        if BanSubstrings:
            self.input_scanners.append(('BanSubstrings', BanSubstrings(substrings=["cookware", "weapon", "harm", "attack"])))

        self.output_scanners = []
        if OutputToxicity:
            self.output_scanners.append(('Toxicity', OutputToxicity(threshold=0.5)))
        if Sensitive:
            self.output_scanners.append(('Sensitive', Sensitive(entity_types=DEFAULT_ENTITY_TYPES + ["DATE_TIME"])))
        if OutputBanTopics:
            self.output_scanners.append(('BanTopics', OutputBanTopics(topics=["violence", "weapons"])))

    async def _run_scanner(self, scanner_callable, text: str, prompt: str = "") -> Tuple[bool, str, str]:
        """Execute a scanner in a thread pool.
        Returns (is_valid, reason, sanitized_text).
        """
        loop = asyncio.get_event_loop()
        # The scanner's .scan() returns (sanitized, is_valid, risk_score) for most
        def _call():
            try:
                import inspect
                sig = inspect.signature(scanner_callable.scan)
                if 'output' in sig.parameters:
                    result = scanner_callable.scan(prompt, text)
                else:
                    result = scanner_callable.scan(text)
                if isinstance(result, tuple) and len(result) == 3:
                    sanitized, is_valid, risk = result
                    reason = f"risk {risk:.2f}" if not is_valid else ""
                else:
                    # Fallback for scanners that just return bool
                    is_valid = bool(result)
                    sanitized = text
                    reason = ""
                return is_valid, reason, sanitized
            except Exception as e:
                # On unexpected error treat as safe but log
                return True, f"error: {e}", text
        return await loop.run_in_executor(None, _call)

    async def scan_input(self, prompt: str) -> GuardResult:
        if not self.input_scanners:
            return GuardResult(passed=True, sanitized_text=prompt)
        for name, scanner in self.input_scanners:
            is_valid, reason, sanitized = await self._run_scanner(scanner, prompt)
            if not is_valid:
                log_violation(category=reason or name, scanner_name=name, input_text=prompt)
                return GuardResult(passed=False, blocked_by=name, reason=reason, sanitized_text=None)
            # Update prompt for next scanner
            prompt = sanitized
        return GuardResult(passed=True, sanitized_text=prompt)

    async def scan_output(self, response: str, prompt: str = "") -> GuardResult:
        if not self.output_scanners:
            return GuardResult(passed=True, sanitized_text=response)
        for name, scanner in self.output_scanners:
            is_valid, reason, sanitized = await self._run_scanner(scanner, response, prompt=prompt)
            if not is_valid:
                log_violation(category=reason or name, scanner_name=name, input_text=response)
                return GuardResult(passed=False, blocked_by=name, reason=reason, sanitized_text=None)
            response = sanitized
        return GuardResult(passed=True, sanitized_text=response)
