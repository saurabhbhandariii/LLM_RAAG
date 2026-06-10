import os
import tempfile
import subprocess
import json
import asyncio
from typing import Tuple
from guards.base import GuardResult, log_violation


class TruffleHogLayer:

    async def scan_text(self, text: str, context: str = "TruffleHog") -> GuardResult:
        if not text.strip():
            return GuardResult(passed=True, sanitized_text=text)

        loop = asyncio.get_event_loop()

        def _call() -> Tuple[bool, str]:
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, "scan.txt")
                with open(filepath, "w") as f:
                    f.write(text)

                env = os.environ.copy()
                env["GIT_PYTHON_REFRESH"] = "quiet"

                try:
                    cmd = ["./venv/bin/trufflehog3", "-f", "JSON", tmpdir]
                    result = subprocess.run(
                        cmd, env=env, capture_output=True, text=True
                    )

                    if result.returncode in [0, 2]:
                        try:
                            output = json.loads(result.stdout)
                            if output:
                                secrets_found = [
                                    item.get("rule", {}).get(
                                        "message", "Unknown Secret"
                                    )
                                    for item in output
                                ]
                                return (
                                    False,
                                    f"Secrets found: {', '.join(secrets_found)}",
                                )
                        except Exception as e:
                            pass
                except Exception as e:
                    import logging

                    logging.error(f"TruffleHog error: {e}")

                return True, ""

        is_valid, reason = await loop.run_in_executor(None, _call)

        if not is_valid:
            log_violation(
                category=reason, scanner_name=f"TruffleHog({context})", input_text=text
            )
            return GuardResult(
                passed=False,
                blocked_by="TruffleHog",
                reason=reason,
                sanitized_text=None,
            )

        return GuardResult(passed=True, sanitized_text=text)

    async def scan_input(self, prompt: str) -> GuardResult:
        return await self.scan_text(prompt, context="Input")

    async def scan_output(self, response: str, prompt: str = "") -> GuardResult:
        return await self.scan_text(response, context="Output")
