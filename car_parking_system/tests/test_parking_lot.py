"""Comprehensive unit tests for the 12-floor, 50 cars/floor parking system."""

from datetime import datetime, timedelta
import os
import tempfile
import unittest

from car_parking_system.fee_calculator import FeeCalculator
from car_parking_system.models import PaymentMethod, TicketStatus, Vehicle
from car_parking_system.parking_lot import ParkingLot
from car_parking_system.storage import ParkingStorage


class TestCarParkingSystem(unittest.TestCase):

    def setUp(self):
        self.fee_calc = FeeCalculator(hourly_rate=40.0, grace_period_minutes=15, daily_max=400.0)
        self.lot = ParkingLot(fee_calculator=self.fee_calc)

    def test_garage_dimensions(self):
        """Test garage has 12 floors and 50 spots per floor (600 total)."""
        self.assertEqual(len(self.lot.floors), 12)
        self.assertEqual(self.lot.TOTAL_FLOORS, 12)
        self.assertEqual(self.lot.SPOTS_PER_FLOOR, 50)
        self.assertEqual(self.lot.TOTAL_CAPACITY, 600)
        self.assertEqual(self.lot.total_occupied, 0)
        self.assertEqual(self.lot.total_free, 600)

        # Check spot IDs on floor 1 and 12
        f1_s1 = self.lot.floors[1].get_spot(1)
        self.assertIsNotNone(f1_s1)
        self.assertEqual(f1_s1.spot_id, "F01-S01")

        f12_s50 = self.lot.floors[12].get_spot(50)
        self.assertIsNotNone(f12_s50)
        self.assertEqual(f12_s50.spot_id, "F12-S50")

    def test_park_vehicle_and_ticket_generation(self):
        """Test parking assigns spots correctly and issues valid tickets."""
        res1 = self.lot.park_vehicle("MH12AB1234", make="Tata", model="Nexon", color="White")
        self.assertEqual(res1["status"], "PARKED")
        self.assertEqual(res1["spot"].spot_id, "F01-S01")
        self.assertEqual(res1["ticket"].license_plate, "MH12AB1234")

        # Second car should go to Spot 2 on Floor 1
        res2 = self.lot.park_vehicle("DL01CD5678", make="Hyundai", model="Creta", color="Black")
        self.assertEqual(res2["status"], "PARKED")
        self.assertEqual(res2["spot"].spot_id, "F01-S02")

        # Car with floor preference
        res3 = self.lot.park_vehicle("KA05EF9999", preferred_floor=7)
        self.assertEqual(res3["status"], "PARKED")
        self.assertEqual(res3["spot"].spot_id, "F07-S01")

    def test_duplicate_plate_rejection(self):
        """Test that duplicate license plates cannot be parked twice."""
        self.lot.park_vehicle("MH12AB1234")
        res_dup = self.lot.park_vehicle("MH12AB1234")
        self.assertEqual(res_dup["status"], "ERROR")
        self.assertIn("already parked", res_dup["message"])

    def test_full_capacity_and_waiting_queue(self):
        """Test queueing behavior when 600 capacity is reached."""
        # Fill all 600 spots
        for floor_num in range(1, 13):
            for spot_num in range(1, 51):
                plate = f"TEST-F{floor_num:02d}-S{spot_num:02d}"
                res = self.lot.park_vehicle(plate)
                self.assertEqual(res["status"], "PARKED")

        self.assertEqual(self.lot.total_occupied, 600)
        self.assertEqual(self.lot.total_free, 0)
        self.assertTrue(self.lot.is_full)

        # 601st car should enter waiting queue
        res_q1 = self.lot.park_vehicle("WAIT01")
        self.assertEqual(res_q1["status"], "QUEUED")
        self.assertEqual(res_q1["queue_position"], 1)
        self.assertEqual(len(self.lot.waiting_queue), 1)

        # 602nd car should be #2 in queue
        res_q2 = self.lot.park_vehicle("WAIT02")
        self.assertEqual(res_q2["status"], "QUEUED")
        self.assertEqual(res_q2["queue_position"], 2)
        self.assertEqual(len(self.lot.waiting_queue), 2)

        # Finding queued car
        find_res = self.lot.find_vehicle("WAIT01")
        self.assertEqual(find_res["status"], "QUEUED")
        self.assertEqual(find_res["queue_position"], 1)

    def test_exit_and_auto_dequeue(self):
        """Test vehicle checkout, fee calculation in ₹, and auto-parking of queued car."""
        # Fill 600 cars
        for floor_num in range(1, 13):
            for spot_num in range(1, 51):
                self.lot.park_vehicle(f"CAR-F{floor_num:02d}-S{spot_num:02d}")

        # Add 1 car to waiting queue
        q_res = self.lot.park_vehicle("QUEUED_CAR", make="Kia", model="Seltos")
        self.assertEqual(q_res["status"], "QUEUED")
        self.assertEqual(len(self.lot.waiting_queue), 1)

        # A car departs from Floor 4 Spot 12
        target_plate = "CAR-F04-S12"
        entry_time = datetime.now() - timedelta(hours=2, minutes=30)
        # Update entry time to test billing
        self.lot.active_tickets_by_plate[target_plate].entry_time = entry_time

        exit_time = datetime.now()
        exit_res = self.lot.exit_vehicle(
            identifier=target_plate,
            payment_method=PaymentMethod.UPI,
            exit_time=exit_time,
        )

        self.assertEqual(exit_res["status"], "SUCCESS")
        # 2h 30m = 3 hours @ ₹40 = ₹120.00
        self.assertEqual(exit_res["fee_inr"], 120.0)
        self.assertEqual(exit_res["formatted_fee"], "₹120.00")
        self.assertEqual(exit_res["payment_method"], "UPI")

        # Verify auto admission
        self.assertIsNotNone(exit_res["auto_admitted"])
        admitted = exit_res["auto_admitted"]
        self.assertEqual(admitted["vehicle"].license_plate, "QUEUED_CAR")
        self.assertEqual(admitted["spot_id"], "F04-S12")
        self.assertEqual(len(self.lot.waiting_queue), 0)

        # Verify queued car is now parked in spot F04-S12
        find_admitted = self.lot.find_vehicle("QUEUED_CAR")
        self.assertEqual(find_admitted["status"], "PARKED")
        self.assertEqual(find_admitted["spot_id"], "F04-S12")

        # Total revenue in ₹
        self.assertEqual(self.lot.total_revenue_inr, 120.0)

    def test_fee_calculator_tiers_inr(self):
        """Test fee calculator logic under various durations in ₹."""
        now = datetime.now()

        # 10 minutes (Grace period <= 15m) -> ₹0.00
        t1 = now - timedelta(minutes=10)
        fee1, dur1, _ = self.fee_calc.calculate_fee(t1, now)
        self.assertEqual(fee1, 0.0)

        # 16 minutes -> 1 hour = ₹40.00
        t2 = now - timedelta(minutes=16)
        fee2, dur2, _ = self.fee_calc.calculate_fee(t2, now)
        self.assertEqual(fee2, 40.0)

        # 2 hours 5 minutes -> 3 hours = ₹120.00
        t3 = now - timedelta(hours=2, minutes=5)
        fee3, dur3, _ = self.fee_calc.calculate_fee(t3, now)
        self.assertEqual(fee3, 120.0)

        # 11 hours -> 11 * 40 = 440, capped at daily_max ₹400.00
        t4 = now - timedelta(hours=11)
        fee4, dur4, _ = self.fee_calc.calculate_fee(t4, now)
        self.assertEqual(fee4, 400.0)

        # 28 hours -> 1 day (₹400) + 4 hours (4 * 40 = 160) = ₹560.00
        t5 = now - timedelta(hours=28)
        fee5, dur5, _ = self.fee_calc.calculate_fee(t5, now)
        self.assertEqual(fee5, 560.0)

    def test_storage_save_and_load(self):
        """Test saving state to JSON and restoring it completely."""
        self.lot.park_vehicle("MH01AA1111", make="Tata", model="Punch")
        self.lot.park_vehicle("MH02BB2222", make="Mahindra", model="Thar", preferred_floor=3)

        # Complete one transaction
        self.lot.exit_vehicle("MH01AA1111", payment_method=PaymentMethod.FASTAG)

        # Queue one vehicle
        self.lot.waiting_queue.enqueue(Vehicle("WAITING99", make="Honda", model="City"))

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            ParkingStorage.save_to_file(self.lot, temp_path)
            loaded_lot = ParkingStorage.load_from_file(temp_path)

            # Check loaded state
            self.assertEqual(loaded_lot.total_occupied, 1)
            find_res = loaded_lot.find_vehicle("MH02BB2222")
            self.assertEqual(find_res["status"], "PARKED")
            self.assertEqual(find_res["floor"], 3)

            # Check transaction loaded
            self.assertEqual(len(loaded_lot.transactions), 1)
            self.assertEqual(loaded_lot.transactions[0].payment_method, PaymentMethod.FASTAG)

            # Check queue loaded
            self.assertEqual(len(loaded_lot.waiting_queue), 1)
            q_res = loaded_lot.find_vehicle("WAITING99")
            self.assertEqual(q_res["status"], "QUEUED")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_payment_methods_support(self):
        """Test all 4 payment methods: UPI, FASTag, Cash, Card."""
        methods = [PaymentMethod.UPI, PaymentMethod.FASTAG, PaymentMethod.CASH, PaymentMethod.CARD]
        past_time = datetime.now() - timedelta(hours=1)

        for idx, method in enumerate(methods):
            plate = f"PAY-CAR-{idx}"
            self.lot.park_vehicle(plate, entry_time=past_time)
            res = self.lot.exit_vehicle(plate, payment_method=method)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertEqual(res["payment_method"], method.value)
            self.assertEqual(res["transaction"].payment_method, method)

        self.assertEqual(len(self.lot.transactions), 4)
        # 4 cars * ₹40 = ₹160.00
        self.assertEqual(self.lot.total_revenue_inr, 160.0)

    def test_vehicle_search_and_queue_cancel(self):
        """Test search for parked, queued, and non-existent vehicles, and queue removal."""
        self.lot.park_vehicle("SEARCH01", make="Tata", model="Safari")

        # Parked vehicle search
        p_res = self.lot.find_vehicle("SEARCH01")
        self.assertEqual(p_res["status"], "PARKED")
        self.assertEqual(p_res["floor"], 1)

        # Non-existent vehicle search
        ne_res = self.lot.find_vehicle("NOTEXIST")
        self.assertEqual(ne_res["status"], "NOT_FOUND")

        # Fill garage and add to queue
        for f in range(1, 13):
            for s in range(1, 51):
                self.lot.park_vehicle(f"FILL-F{f}-S{s}")

        self.lot.park_vehicle("QUEUE_LEAVER")
        q_res = self.lot.find_vehicle("QUEUE_LEAVER")
        self.assertEqual(q_res["status"], "QUEUED")

        # Cancel queue
        removed = self.lot.cancel_queue("QUEUE_LEAVER")
        self.assertTrue(removed)
        after_cancel = self.lot.find_vehicle("QUEUE_LEAVER")
        self.assertEqual(after_cancel["status"], "NOT_FOUND")

    def test_occupancy_dashboard_data(self):
        """Test get_floor_occupancy returns data for all 12 floors."""
        # Park 10 cars on floor 1, 20 cars on floor 2
        for i in range(1, 11):
            self.lot.park_vehicle(f"F1-C{i}", preferred_floor=1)
        for i in range(1, 21):
            self.lot.park_vehicle(f"F2-C{i}", preferred_floor=2)

        stats = self.lot.get_floor_occupancy()
        self.assertEqual(len(stats), 12)
        self.assertEqual(stats[0]["floor"], 1)
        self.assertEqual(stats[0]["occupied"], 10)
        self.assertEqual(stats[0]["free"], 40)
        self.assertEqual(stats[0]["percentage"], 20.0)

        self.assertEqual(stats[1]["floor"], 2)
        self.assertEqual(stats[1]["occupied"], 20)
        self.assertEqual(stats[1]["free"], 30)
        self.assertEqual(stats[1]["percentage"], 40.0)

        # Floor 12 should be empty
        self.assertEqual(stats[11]["floor"], 12)
        self.assertEqual(stats[11]["occupied"], 0)
        self.assertEqual(stats[11]["free"], 50)


if __name__ == "__main__":
    unittest.main()

