"""State persistence module for the Car Parking System using JSON."""

from datetime import datetime
import json
import os
from typing import Optional

from .fee_calculator import FeeCalculator
from .models import ParkingSpot, PaymentMethod, Ticket, TicketStatus, Transaction, Vehicle
from .parking_lot import ParkingLot


class ParkingStorage:
    """Handles saving and loading the parking facility state to/from a JSON file."""

    DEFAULT_FILENAME = "parking_state.json"

    @classmethod
    def save_to_file(cls, parking_lot: ParkingLot, filepath: Optional[str] = None) -> str:
        target_path = filepath or cls.DEFAULT_FILENAME

        # Collect occupied spots
        spots_data = []
        for floor_num in range(1, parking_lot.TOTAL_FLOORS + 1):
            floor = parking_lot.floors[floor_num]
            for spot_num, spot in floor.spots.items():
                if spot.is_occupied and spot.current_vehicle:
                    spots_data.append({
                        "floor": spot.floor,
                        "spot_number": spot.spot_number,
                        "vehicle": spot.current_vehicle.to_dict(),
                    })

        # Collect tickets
        tickets_data = [t.to_dict() for t in parking_lot.active_tickets_by_id.values()]

        # Collect waiting queue
        queue_data = []
        for item in parking_lot.waiting_queue.list_waiting():
            queue_data.append({
                "license_plate": item["license_plate"],
                "make": item["make"],
                "model": item["model"],
                "color": item["color"],
                "entry_time": item["entry_time"].isoformat(),
                "preferred_floor": item["preferred_floor"],
            })

        # Collect transactions
        transactions_data = [txn.to_dict() for txn in parking_lot.transactions]

        data = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "occupied_spots": spots_data,
            "active_tickets": tickets_data,
            "waiting_queue": queue_data,
            "transactions": transactions_data,
            "rates": {
                "hourly_rate": parking_lot.fee_calculator.hourly_rate,
                "grace_period_minutes": parking_lot.fee_calculator.grace_period_minutes,
                "daily_max": parking_lot.fee_calculator.daily_max,
            },
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return target_path

    @classmethod
    def load_from_file(cls, filepath: Optional[str] = None) -> ParkingLot:
        target_path = filepath or cls.DEFAULT_FILENAME
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"State file not found: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rates = data.get("rates", {})
        fee_calc = FeeCalculator(
            hourly_rate=rates.get("hourly_rate", 40.0),
            grace_period_minutes=rates.get("grace_period_minutes", 15),
            daily_max=rates.get("daily_max", 400.0),
        )

        parking_lot = ParkingLot(fee_calculator=fee_calc)

        # Restore occupied spots
        for spot_item in data.get("occupied_spots", []):
            floor_num = spot_item["floor"]
            spot_num = spot_item["spot_number"]
            veh = Vehicle.from_dict(spot_item["vehicle"])
            spot = parking_lot.floors[floor_num].get_spot(spot_num)
            if spot:
                spot.park(veh)

        # Restore active tickets
        for t_item in data.get("active_tickets", []):
            ticket = Ticket.from_dict(t_item)
            parking_lot.active_tickets_by_id[ticket.ticket_id] = ticket
            parking_lot.active_tickets_by_plate[ticket.license_plate] = ticket

        # Restore waiting queue
        for q_item in data.get("waiting_queue", []):
            veh = Vehicle(
                license_plate=q_item["license_plate"],
                make=q_item.get("make", "Generic"),
                model=q_item.get("model", "Car"),
                color=q_item.get("color", "Unknown"),
                entry_time=datetime.fromisoformat(q_item["entry_time"]),
            )
            parking_lot.waiting_queue.enqueue(veh, q_item.get("preferred_floor"))

        # Restore transactions
        for txn_item in data.get("transactions", []):
            txn = Transaction.from_dict(txn_item)
            parking_lot.transactions.append(txn)

        return parking_lot
