"""Fee and billing calculator in Indian Rupees (₹)."""

from datetime import datetime
import math
from typing import Optional, Tuple


class FeeCalculator:
    """Calculates parking charges in Indian Rupees (₹).

    Default Fee Structure:
      - Complimentary Grace Period: First 15 minutes = ₹0.00
      - Hourly Rate: ₹40.00 per hour (or fraction thereof)
      - Daily Maximum Cap: ₹400.00 per 24-hour block
    """

    def __init__(
        self,
        hourly_rate: float = 40.0,
        grace_period_minutes: int = 15,
        daily_max: float = 400.0,
    ):
        self.hourly_rate = hourly_rate
        self.grace_period_minutes = grace_period_minutes
        self.daily_max = daily_max

    def calculate_fee(
        self, entry_time: datetime, exit_time: Optional[datetime] = None
    ) -> Tuple[float, str, int]:
        """Calculate parking fee based on duration.

        Returns:
            Tuple of:
              - fee_inr (float): Total payable amount in ₹
              - duration_str (str): Human-readable duration (e.g. '2h 15m')
              - total_minutes (int): Total parking duration in minutes
        """
        if exit_time is None:
            exit_time = datetime.now()

        elapsed = exit_time - entry_time
        total_seconds = max(0, int(elapsed.total_seconds()))
        total_minutes = math.ceil(total_seconds / 60)

        # Build readable duration string
        days, rem_minutes = divmod(total_minutes, 1440)
        hours, minutes = divmod(rem_minutes, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        duration_str = " ".join(parts) if parts else "0m"

        # Check grace period
        if total_minutes <= self.grace_period_minutes:
            return 0.0, duration_str, total_minutes

        # Multi-day and hourly calculation
        # Full 24-hour days capped at daily_max
        fee = days * self.daily_max

        # Remaining hours in the current day
        remaining_hours = math.ceil(rem_minutes / 60)
        sub_day_fee = remaining_hours * self.hourly_rate

        # Capped by daily max if applicable
        fee += min(sub_day_fee, self.daily_max)

        return round(fee, 2), duration_str, total_minutes

    @staticmethod
    def format_inr(amount: float) -> str:
        """Format an amount into Indian Rupees representation (e.g. ₹120.00)."""
        return f"₹{amount:,.2f}"
