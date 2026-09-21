"""Simulation helper for traffic generation, demonstrations, and load testing."""

from datetime import datetime, timedelta
import random
from typing import List, Optional

from .models import PaymentMethod, Vehicle
from .parking_lot import ParkingLot

STATE_CODES = ["MH", "DL", "KA", "HR", "TN", "UP", "GJ", "TS", "WB", "KL"]
CAR_MAKES = [
    ("Tata", ["Nexon", "Harrier", "Punch", "Safari", "Tiago"]),
    ("Hyundai", ["Creta", "Venue", "i20", "Verna", "Tucson"]),
    ("Maruti Suzuki", ["Swift", "Baleno", "Brezza", "Ertiga", "Dzire"]),
    ("Mahindra", ["XUV700", "Scorpio-N", "Thar", "XUV300", "Bolero"]),
    ("Honda", ["City", "Amaze", "Elevate"]),
    ("Toyota", ["Innova Crysta", "Fortuner", "Hyryder", "Glanza"]),
    ("Kia", ["Seltos", "Sonet", "Carens", "EV6"]),
]
COLORS = ["White", "Silver", "Grey", "Black", "Red", "Blue", "Brown"]


def generate_random_plate(existing_plates: Optional[set] = None) -> str:
    """Generates a realistic Indian vehicle registration number."""
    existing = existing_plates or set()
    while True:
        state = random.choice(STATE_CODES)
        rto = random.randint(1, 99)
        series = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
        number = random.randint(1000, 9999)
        plate = f"{state}{rto:02d}{series}{number}"
        if plate not in existing:
            return plate


def generate_random_vehicle(existing_plates: Optional[set] = None, entry_time: Optional[datetime] = None) -> Vehicle:
    """Generates a random vehicle with realistic specs and timestamp."""
    plate = generate_random_plate(existing_plates)
    make, models = random.choice(CAR_MAKES)
    model = random.choice(models)
    color = random.choice(COLORS)
    time = entry_time or (datetime.now() - timedelta(minutes=random.randint(15, 360)))
    return Vehicle(
        license_plate=plate,
        make=make,
        model=model,
        color=color,
        entry_time=time,
    )


def prefill_parking_lot(parking_lot: ParkingLot, count: int = 595) -> int:
    """Fills the garage with up to `count` cars to test high occupancy and queueing."""
    actual_count = min(count, parking_lot.TOTAL_CAPACITY)
    existing_plates = set(parking_lot.active_tickets_by_plate.keys())

    parked_count = 0
    now = datetime.now()

    for _ in range(actual_count - parking_lot.total_occupied):
        # Staggered entry times between 30 mins and 5 hours ago
        past_minutes = random.randint(30, 300)
        veh_time = now - timedelta(minutes=past_minutes)
        veh = generate_random_vehicle(existing_plates, entry_time=veh_time)
        existing_plates.add(veh.license_plate)

        res = parking_lot.park_vehicle(
            license_plate=veh.license_plate,
            make=veh.make,
            model=veh.model,
            color=veh.color,
            entry_time=veh.entry_time,
        )
        if res["status"] == "PARKED":
            parked_count += 1

    return parked_count
