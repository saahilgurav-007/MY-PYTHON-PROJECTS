import argparse
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from car_parking_system.cli import ParkingCLI
from car_parking_system.fee_calculator import FeeCalculator
from car_parking_system.models import PaymentMethod
from car_parking_system.parking_lot import ParkingLot
from car_parking_system.simulation import generate_random_vehicle, prefill_parking_lot


def run_demo():
    """Runs a quick non-interactive demonstration of the parking, queue, and ₹ payments."""
    print("=" * 70)
    print("🚗 DEMO: 12 FLOORS | 50 CARS/FLOOR | FIFO QUEUE | INR (₹) PAYMENTS")
    print("=" * 70)

    fee_calc = FeeCalculator(hourly_rate=40.0, grace_period_minutes=15)
    lot = ParkingLot(fee_calculator=fee_calc)

    print("\n1. Initializing Parking Garage...")
    print(f"   Floors: {lot.TOTAL_FLOORS} | Spots per floor: {lot.SPOTS_PER_FLOOR} | Capacity: {lot.TOTAL_CAPACITY}")

    print("\n2. Prefilling 598 spots with vehicles...")
    prefill_parking_lot(lot, count=598)
    print(f"   Current Occupancy: {lot.total_occupied}/{lot.TOTAL_CAPACITY} (Free: {lot.total_free})")

    print("\n3. Parking 2 more cars to fill the garage to 100% (600/600)...")
    from datetime import datetime, timedelta
    past_entry = datetime.now() - timedelta(hours=2, minutes=15)
    res1 = lot.park_vehicle("MH12AB9001", make="Tata", model="Nexon", color="White", entry_time=past_entry)
    res2 = lot.park_vehicle("DL03CD9002", make="Hyundai", model="Creta", color="Black")
    print(f"   Car 599: {res1['message']}")
    print(f"   Car 600: {res2['message']}")
    print(f"   Garage is now FULL: {lot.is_full} ({lot.total_occupied}/600)")

    print("\n4. Car 601 and Car 602 arrive while garage is FULL (Testing FIFO Queue)...")
    q1 = lot.park_vehicle("KA05EF9003", make="Mahindra", model="Thar", color="Red")
    q2 = lot.park_vehicle("HR26GH9004", make="Kia", model="Seltos", color="Blue")
    print(f"   Car 601: {q1['message']}")
    print(f"   Car 602: {q2['message']}")
    print(f"   Waiting Queue Size: {len(lot.waiting_queue)}")

    print("\n5. Searching for queued car KA05EF9003...")
    search_q = lot.find_vehicle("KA05EF9003")
    print(f"   Found Status: {search_q['status']} | Queue Position: #{search_q['queue_position']}")

    print("\n6. Simulating exit of Car MH12AB9001 with UPI Payment in ₹...")
    exit_res = lot.exit_vehicle("MH12AB9001", payment_method=PaymentMethod.UPI)
    print(f"   Exit Status: {exit_res['status']}")
    print(f"   Fee Paid: {exit_res['formatted_fee']} ({exit_res['duration_str']}) via {exit_res['payment_method']}")
    print(f"   Transaction ID: {exit_res['transaction'].txn_id}")

    if exit_res.get("auto_admitted"):
        admitted = exit_res["auto_admitted"]
        print(f"\n   🎉 FIFO QUEUE AUTO-ADMISSION TRIGGERED:")
        print(f"   Car '{admitted['vehicle'].license_plate}' automatically admitted from queue!")
        print(f"   Allocated Spot: {admitted['spot_id']} (Floor {admitted['floor']})")
        print(f"   Remaining Queue Size: {len(lot.waiting_queue)}")

    print("\n7. Total Revenue Collected:")
    print(f"   Total Revenue: {lot.fee_calculator.format_inr(lot.total_revenue_inr)}")

    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE! All 12 floors, 50 spots/floor, queue, and ₹ payments verified.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Multi-Floor Car Queue & Parking System (12 Floors, 50 Cars/Floor)")
    parser.add_argument("--demo", action="store_true", help="Run automated demonstration script")
    parser.add_argument("--fill", type=int, default=0, help="Pre-fill garage with N vehicles on start")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    lot = ParkingLot()
    if args.fill > 0:
        added = prefill_parking_lot(lot, count=args.fill)
        print(f"Pre-filled {added} vehicles into parking lot.")

    cli = ParkingCLI(lot)
    cli.run()


if __name__ == "__main__":
    main()
