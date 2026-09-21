"""Safety guardrails and verification for desktop automation actions."""

from typing import Callable, Optional
from ..nlp.intent_types import RiskLevel, IntentResult

class SafetyGuard:
    """Manages risk verification, destructive confirmations, and dry-run execution."""

    def __init__(self, confirmation_callback: Optional[Callable[[str], bool]] = None):
        """
        confirmation_callback: A function taking a prompt string and returning bool.
        If None, default to auto-approving or terminal prompt.
        """
        self.confirmation_callback = confirmation_callback

    def verify_action(self, intent_result: IntentResult, dry_run: bool = False, force: bool = False) -> tuple[bool, str]:
        """
        Checks if action should proceed.
        Returns: (can_proceed: bool, reason: str)
        """
        if dry_run:
            return True, "Dry-run mode active. No actual modifications will be made."

        if intent_result.risk_level != RiskLevel.DESTRUCTIVE:
            return True, "Action deemed safe."

        if force:
            return True, "Bypassed confirmation via force flag."

        warning_message = (
            f"CAUTION: Command '{intent_result.raw_text}' is categorized as DESTRUCTIVE "
            f"({intent_result.intent.value})."
        )

        if self.confirmation_callback:
            approved = self.confirmation_callback(warning_message)
            if approved:
                return True, "User confirmed destructive action."
            return False, "Action cancelled by user confirmation."

        # Default fallback if no callback provided:
        return True, "Confirmation callback omitted; proceeding under supervision."
