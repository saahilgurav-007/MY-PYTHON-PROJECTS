"""Core Parking Lot and Queue Management Implementation.

Manages 12 floors, 50 cars per floor (total 600 cars),
FIFO waiting queue, vehicle admissions, departures, and ₹ transactions.
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

from .fee_calculator import FeeCalculator
from .models import ParkingSpot, PaymentMethod, Ticket, TicketStatus, Transaction, Vehicle


class ParkingFloor:
    """Represents a single floor in the parking facility."""

    def __init__(self, floor_number: int, capacity: int = 50):
        self.floor_number = floor_number
        self.capacity = capacity
        # Spots 1 to capacity
        self.spots: Dict[int, ParkingSpot] = {
            num: ParkingSpot(floor=floor_number, spot_number=num)
            for num in range(1, capacity + 1)
        }

    @property
    def occupied_count(self) -> int:
        return sum(1 for spot in self.spots.values() if spot.is_occupied)

    @property
    def free_count(self) -> int:
        return self.capacity - self.occupied_count

    @property
    def is_full(self) -> bool:
        return self.free_count == 0

    def find_available_spot(self) -> Optional[ParkingSpot]:
        """Returns the first available spot (lowest spot number) on this floor."""
        for num in range(1, self.capacity + 1):
            spot = self.spots[num]
            if not spot.is_occupied:
                return spot
        return None

    def get_spot(self, spot_number: int) -> Optional[ParkingSpot]:
        return self.spots.get(spot_number)


class WaitingQueue:
    """FIFO queue for cars waiting to enter when parking is full."""

    def __init__(self):
        # Stores tuples of (Vehicle, preferred_floor)
        self._queue: deque[Tuple[Vehicle, Optional[int]]] = deque()

    def enqueue(self, vehicle: Vehicle, preferred_floor: Optional[int] = None) -> int:
        """Adds a car to the end of the queue. Returns 1-based queue position."""
        self._queue.append((vehicle, preferred_floor))
        return len(self._queue)

    def dequeue(self) -> Optional[Tuple[Vehicle, Optional[int]]]:
        """Pops the next waiting car from the front of the queue."""
        if self._queue:
            return self._queue.popleft()
        return None

    def remove(self, license_plate: str) -> bool:
        """Removes a vehicle from anywhere in the queue if the driver leaves."""
        plate = license_plate.strip().upper()
        for idx, (veh, pref) in enumerate(self._queue):
            if veh.license_plate == plate:
                del self._queue[idx]
                return True
        return False

    def find_position(self, license_plate: str) -> Optional[Tuple[int, Vehicle]]:
        """Finds 1-based position and vehicle in the queue by license plate."""
        plate = license_plate.strip().upper()
        for idx, (veh, _) in enumerate(self._queue):
            if veh.license_plate == plate:
                return (idx + 1, veh)
        return None

    def list_waiting(self) -> List[dict]:
        """Returns snapshot of all cars currently waiting in queue."""
        results = []
        now = datetime.now()
        for pos, (veh, pref) in enumerate(self._queue, start=1):
            wait_time_minutes = max(0, int((now - veh.entry_time).total_seconds() // 60))
            results.append({
                "position": pos,
                "license_plate": veh.license_plate,
                "make": veh.make,
                "model": veh.model,
                "color": veh.color,
                "entry_time": veh.entry_time,
                "wait_minutes": wait_time_minutes,
                "preferred_floor": pref,
            })
        return results

    def __len__(self) -> int:
        return len(self._queue)


class ParkingLot:
    """Manages the 12-floor parking facility (50 spots/floor, total 600 spots)."""

    TOTAL_FLOORS = 12
    SPOTS_PER_FLOOR = 50
    TOTAL_CAPACITY = TOTAL_FLOORS * SPOTS_PER_FLOOR

    def __init__(self, fee_calculator: Optional[FeeCalculator] = None):
        self.fee_calculator = fee_calculator or FeeCalculator()
        self.floors: Dict[int, ParkingFloor] = {
            floor_num: ParkingFloor(floor_number=floor_num, capacity=self.SPOTS_PER_FLOOR)
            for floor_num in range(1, self.TOTAL_FLOORS + 1)
        }
        self.waiting_queue = WaitingQueue()
        # Active tickets mapped by ticket_id and license_plate
        self.active_tickets_by_id: Dict[str, Ticket] = {}
        self.active_tickets_by_plate: Dict[str, Ticket] = {}
        # Transaction history
        self.transactions: List[Transaction] = []

    @property
    def total_occupied(self) -> int:
        return sum(floor.occupied_count for floor in self.floors.values())

    @property
    def total_free(self) -> int:
        return self.TOTAL_CAPACITY - self.total_occupied

    @property
    def is_full(self) -> bool:
        return self.total_occupied >= self.TOTAL_CAPACITY

    @property
    def total_revenue_inr(self) -> float:
        return round(sum(t.amount_inr for t in self.transactions), 2)

    def park_vehicle(
        self,
        license_plate: str,
        make: str = "Generic",
        model: str = "Car",
        color: str = "Unknown",
        preferred_floor: Optional[int] = None,
        entry_time: Optional[datetime] = None,
    ) -> dict:
        """Processes vehicle arrival.

        Parks in an available spot or places in FIFO WaitingQueue if full.
        """
        plate = license_plate.strip().upper()
        if not plate:
            return {"status": "ERROR", "message": "License plate cannot be empty."}

        # Check if already parked
        if plate in self.active_tickets_by_plate:
            ticket = self.active_tickets_by_plate[plate]
            return {
                "status": "ERROR",
                "message": f"Vehicle with plate '{plate}' is already parked at Spot {ticket.spot_id}.",
                "ticket": ticket,
            }

        # Check if already in waiting queue
        queue_pos = self.waiting_queue.find_position(plate)
        if queue_pos:
            pos, _ = queue_pos
            return {
                "status": "ERROR",
                "message": f"Vehicle '{plate}' is already in waiting queue at position #{pos}.",
            }

        vehicle = Vehicle(
            license_plate=plate,
            make=make,
            model=model,
            color=color,
            entry_time=entry_time or datetime.now(),
        )

        # Validate preferred floor
        if preferred_floor is not None and (preferred_floor < 1 or preferred_floor > self.TOTAL_FLOORS):
            preferred_floor = None

        # Try to find a spot
        spot = self._find_best_spot(preferred_floor)

        if spot is not None:
            # Park vehicle
            spot.park(vehicle)
            ticket = Ticket.create(vehicle, spot)
            self.active_tickets_by_id[ticket.ticket_id] = ticket
            self.active_tickets_by_plate[plate] = ticket

            return {
                "status": "PARKED",
                "message": f"Vehicle '{plate}' parked successfully at Spot {spot.spot_id} (Floor {spot.floor}).",
                "ticket": ticket,
                "spot": spot,
                "vehicle": vehicle,
            }
        else:
            # Facility is completely full: Add to FIFO waiting queue
            position = self.waiting_queue.enqueue(vehicle, preferred_floor)
            return {
                "status": "QUEUED",
                "message": f"Parking is FULL (600/600 spots occupied). Vehicle '{plate}' joined waiting queue at position #{position}.",
                "queue_position": position,
                "vehicle": vehicle,
            }

    def _find_best_spot(self, preferred_floor: Optional[int] = None) -> Optional[ParkingSpot]:
        """Finds spot based on floor preference, or lowest floor with open spots."""
        # 1. Try preferred floor first if requested
        if preferred_floor and not self.floors[preferred_floor].is_full:
            spot = self.floors[preferred_floor].find_available_spot()
            if spot:
                return spot

        # 2. Sequential search from Floor 1 to Floor 12
        for floor_num in range(1, self.TOTAL_FLOORS + 1):
            floor = self.floors[floor_num]
            if not floor.is_full:
                spot = floor.find_available_spot()
                if spot:
                    return spot

        return None

    def exit_vehicle(
        self,
        identifier: str,
        payment_method: PaymentMethod = PaymentMethod.UPI,
        exit_time: Optional[datetime] = None,
    ) -> dict:
        """Processes vehicle departure, computes ₹ fee, generates receipt,

        and auto-assigns the newly vacant spot to the next waiting car in queue.
        """
        id_str = identifier.strip().upper()
        ticket: Optional[Ticket] = None

        if id_str in self.active_tickets_by_plate:
            ticket = self.active_tickets_by_plate[id_str]
        elif id_str in self.active_tickets_by_id:
            ticket = self.active_tickets_by_id[id_str]

        if not ticket:
            return {
                "status": "ERROR",
                "message": f"No active vehicle or ticket found matching '{identifier}'.",
            }

        now = exit_time or datetime.now()
        if now < ticket.entry_time:
            now = ticket.entry_time

        # Calculate billing in INR (₹)
        fee_inr, duration_str, duration_minutes = self.fee_calculator.calculate_fee(
            ticket.entry_time, now
        )

        # Generate Transaction
        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        transaction = Transaction(
            txn_id=txn_id,
            ticket_id=ticket.ticket_id,
            license_plate=ticket.license_plate,
            entry_time=ticket.entry_time,
            exit_time=now,
            duration_minutes=duration_minutes,
            amount_inr=fee_inr,
            payment_method=payment_method,
            timestamp=now,
        )
        self.transactions.append(transaction)

        # Free the parking spot
        floor = self.floors[ticket.floor]
        spot = floor.get_spot(ticket.spot_number)
        exiting_vehicle = None
        if spot:
            exiting_vehicle = spot.vacate()

        # Update ticket status and cleanup active indices
        ticket.status = TicketStatus.PAID
        self.active_tickets_by_id.pop(ticket.ticket_id, None)
        self.active_tickets_by_plate.pop(ticket.license_plate, None)

        # Check FIFO waiting queue for auto-allocation
        auto_admitted_info = None
        if len(self.waiting_queue) > 0:
            next_entry = self.waiting_queue.dequeue()
            if next_entry:
                queued_vehicle, queued_pref = next_entry
                # Allocate best spot (now at least the freed spot is available)
                new_spot = self._find_best_spot(queued_pref)
                if new_spot:
                    # Car gets admitted at the current exit timestamp
                    queued_vehicle.entry_time = now
                    new_spot.park(queued_vehicle)
                    new_ticket = Ticket.create(queued_vehicle, new_spot)
                    self.active_tickets_by_id[new_ticket.ticket_id] = new_ticket
                    self.active_tickets_by_plate[queued_vehicle.license_plate] = new_ticket
                    auto_admitted_info = {
                        "vehicle": queued_vehicle,
                        "ticket": new_ticket,
                        "spot_id": new_spot.spot_id,
                        "floor": new_spot.floor,
                        "spot_number": new_spot.spot_number,
                    }

        return {
            "status": "SUCCESS",
            "message": f"Vehicle '{ticket.license_plate}' checked out successfully.",
            "transaction": transaction,
            "ticket": ticket,
            "fee_inr": fee_inr,
            "formatted_fee": self.fee_calculator.format_inr(fee_inr),
            "duration_str": duration_str,
            "duration_minutes": duration_minutes,
            "payment_method": payment_method.value,
            "auto_admitted": auto_admitted_info,
        }

    def find_vehicle(self, license_plate: str) -> dict:
        """Finds a vehicle's current location or queue position."""
        plate = license_plate.strip().upper()
        if not plate:
            return {"status": "NOT_FOUND", "message": "License plate cannot be empty."}

        # Check parked
        if plate in self.active_tickets_by_plate:
            ticket = self.active_tickets_by_plate[plate]
            now = datetime.now()
            fee_inr, duration_str, duration_minutes = self.fee_calculator.calculate_fee(
                ticket.entry_time, now
            )
            spot = self.floors[ticket.floor].get_spot(ticket.spot_number)
            vehicle = spot.current_vehicle if spot else None

            return {
                "status": "PARKED",
                "license_plate": plate,
                "floor": ticket.floor,
                "spot_number": ticket.spot_number,
                "spot_id": ticket.spot_id,
                "ticket_id": ticket.ticket_id,
                "entry_time": ticket.entry_time,
                "current_duration": duration_str,
                "accrued_fee": self.fee_calculator.format_inr(fee_inr),
                "vehicle": vehicle,
            }

        # Check waiting queue
        queue_result = self.waiting_queue.find_position(plate)
        if queue_result:
            pos, vehicle = queue_result
            wait_minutes = max(0, int((datetime.now() - vehicle.entry_time).total_seconds() // 60))
            return {
                "status": "QUEUED",
                "license_plate": plate,
                "queue_position": pos,
                "total_waiting": len(self.waiting_queue),
                "wait_minutes": wait_minutes,
                "vehicle": vehicle,
            }

        return {
            "status": "NOT_FOUND",
            "message": f"Vehicle with plate '{plate}' is not parked or queued.",
        }

    def cancel_queue(self, license_plate: str) -> bool:
        """Removes a vehicle from the waiting queue if requested."""
        return self.waiting_queue.remove(license_plate)

    def get_floor_occupancy(self) -> List[dict]:
        """Returns statistics for all 12 floors."""
        result = []
        for floor_num in range(1, self.TOTAL_FLOORS + 1):
            floor = self.floors[floor_num]
            occ = floor.occupied_count
            cap = floor.capacity
            pct = (occ / cap * 100.0) if cap > 0 else 0.0
            result.append({
                "floor": floor_num,
                "occupied": occ,
                "free": floor.free_count,
                "capacity": cap,
                "percentage": round(pct, 1),
            })
        return result

    def get_summary(self) -> dict:
        """Returns facility-wide overview."""
        return {
            "total_capacity": self.TOTAL_CAPACITY,
            "total_occupied": self.total_occupied,
            "total_free": self.total_free,
            "occupancy_rate": round(self.total_occupied / self.TOTAL_CAPACITY * 100.0, 1),
            "waiting_queue_length": len(self.waiting_queue),
            "total_transactions": len(self.transactions),
            "total_revenue_inr": self.total_revenue_inr,
            "formatted_revenue": self.fee_calculator.format_inr(self.total_revenue_inr),
        }
