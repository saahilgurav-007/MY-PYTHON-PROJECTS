"""Domain models for the Car Queue and Parking System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class PaymentMethod(str, Enum):
    UPI = "UPI"
    FASTAG = "FASTag"
    CASH = "Cash"
    CARD = "Card"


class TicketStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


@dataclass
class Vehicle:
    """Represents a car entering or waiting in the parking system."""
    license_plate: str
    make: str = "Generic"
    model: str = "Car"
    color: str = "Unknown"
    entry_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.license_plate = self.license_plate.strip().upper()

    def to_dict(self) -> dict:
        return {
            "license_plate": self.license_plate,
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "entry_time": self.entry_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Vehicle":
        return cls(
            license_plate=data["license_plate"],
            make=data.get("make", "Generic"),
            model=data.get("model", "Car"),
            color=data.get("color", "Unknown"),
            entry_time=datetime.fromisoformat(data["entry_time"]),
        )


@dataclass
class ParkingSpot:
    """Represents an individual parking spot on a specific floor."""
    floor: int
    spot_number: int
    is_occupied: bool = False
    current_vehicle: Optional[Vehicle] = None

    @property
    def spot_id(self) -> str:
        """Standard spot identifier formatted as F01-S01 to F12-S50."""
        return f"F{self.floor:02d}-S{self.spot_number:02d}"

    def park(self, vehicle: Vehicle) -> None:
        self.current_vehicle = vehicle
        self.is_occupied = True

    def vacate(self) -> Optional[Vehicle]:
        vehicle = self.current_vehicle
        self.current_vehicle = None
        self.is_occupied = False
        return vehicle

    def to_dict(self) -> dict:
        return {
            "floor": self.floor,
            "spot_number": self.spot_number,
            "is_occupied": self.is_occupied,
            "current_vehicle": self.current_vehicle.to_dict() if self.current_vehicle else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParkingSpot":
        spot = cls(
            floor=data["floor"],
            spot_number=data["spot_number"],
            is_occupied=data["is_occupied"],
            current_vehicle=Vehicle.from_dict(data["current_vehicle"]) if data.get("current_vehicle") else None,
        )
        return spot


@dataclass
class Ticket:
    """Digital parking ticket issued upon successful parking allocation."""
    ticket_id: str
    license_plate: str
    spot_id: str
    floor: int
    spot_number: int
    entry_time: datetime = field(default_factory=datetime.now)
    status: TicketStatus = TicketStatus.ACTIVE

    @classmethod
    def create(cls, vehicle: Vehicle, spot: ParkingSpot) -> "Ticket":
        tid = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        return cls(
            ticket_id=tid,
            license_plate=vehicle.license_plate,
            spot_id=spot.spot_id,
            floor=spot.floor,
            spot_number=spot.spot_number,
            entry_time=vehicle.entry_time,
            status=TicketStatus.ACTIVE,
        )

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "license_plate": self.license_plate,
            "spot_id": self.spot_id,
            "floor": self.floor,
            "spot_number": self.spot_number,
            "entry_time": self.entry_time.isoformat(),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        return cls(
            ticket_id=data["ticket_id"],
            license_plate=data["license_plate"],
            spot_id=data["spot_id"],
            floor=data["floor"],
            spot_number=data["spot_number"],
            entry_time=datetime.fromisoformat(data["entry_time"]),
            status=TicketStatus(data.get("status", TicketStatus.ACTIVE.value)),
        )


@dataclass
class Transaction:
    """Record of parking payment transaction in Indian Rupees (₹)."""
    txn_id: str
    ticket_id: str
    license_plate: str
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    amount_inr: float
    payment_method: PaymentMethod
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "txn_id": self.txn_id,
            "ticket_id": self.ticket_id,
            "license_plate": self.license_plate,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "amount_inr": self.amount_inr,
            "payment_method": self.payment_method.value,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            txn_id=data["txn_id"],
            ticket_id=data["ticket_id"],
            license_plate=data["license_plate"],
            entry_time=datetime.fromisoformat(data["entry_time"]),
            exit_time=datetime.fromisoformat(data["exit_time"]),
            duration_minutes=data["duration_minutes"],
            amount_inr=float(data["amount_inr"]),
            payment_method=PaymentMethod(data["payment_method"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
