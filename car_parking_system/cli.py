from datetime import datetime
import sys
from typing import Optional

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

from .fee_calculator import FeeCalculator
from .models import PaymentMethod
from .parking_lot import ParkingLot
from .simulation import generate_random_vehicle, prefill_parking_lot
from .storage import ParkingStorage


def _render_progress_bar(occupied: int, capacity: int, width: int = 20) -> str:
    """Generates an ASCII progress bar for occupancy."""
    if capacity <= 0:
        return "[" + "░" * width + "]"
    fill_ratio = min(1.0, max(0.0, occupied / capacity))
    fill_chars = int(round(fill_ratio * width))
    empty_chars = width - fill_chars
    return "[" + ("█" * fill_chars) + ("░" * empty_chars) + "]"


class ParkingCLI:
    """Terminal user interface for managing the parking facility."""

    def __init__(self, parking_lot: Optional[ParkingLot] = None):
        self.lot = parking_lot or ParkingLot()

    def print_header(self):
        summary = self.lot.get_summary()
        occ_bar = _render_progress_bar(summary["total_occupied"], summary["total_capacity"], 25)

        print("\n" + "═" * 76)
        print("  🚗 MULTI-FLOOR CAR QUEUE & PARKING SYSTEM (12 FLOORS | 600 SPOTS)")
        print("                 Billing & Transactions in INR (₹)                ")
        print("═" * 76)
        print(f" Total Occupied : {summary['total_occupied']:>3} / {summary['total_capacity']} {occ_bar} ({summary['occupancy_rate']}%)")
        print(f" Available Spots: {summary['total_free']:>3} spots free")
        print(f" Waiting Queue  : {summary['waiting_queue_length']:>3} vehicles waiting")
        print(f" Total Revenue  : {summary['formatted_revenue']} (Completed Transactions: {summary['total_transactions']})")
        print("─" * 76)

    def print_menu(self):
        print("\nSelect an action:")
        print("  [1]  📥 Park Vehicle (Entry Gate / FIFO Queue if Full)")
        print("  [2]  📤 Exit Vehicle & Process Payment in ₹ (UPI/FASTag/Cash/Card)")
        print("  [3]  🔍 Search Vehicle (by License Plate)")
        print("  [4]  🏢 View 12-Floor Real-Time Capacity Dashboard")
        print("  [5]  🗺️  View Specific Floor Spot Grid (Spots 1 to 50)")
        print("  [6]  ⏳ View Waiting Queue (Vehicles awaiting spot)")
        print("  [7]  💳 View Payment Transactions & Total Revenue (₹)")
        print("  [8]  ⚡ Quick Simulation / Auto-fill (Test High Occupancy & Queue)")
        print("  [9]  💾 Save / Load System State (JSON)")
        print("  [0]  🚪 Exit Application")
        print("─" * 76)

    def handle_park(self):
        print("\n--- [1] VEHICLE ENTRY GATE ---")
        plate = input("Enter License Plate (e.g. MH12AB1234): ").strip()
        if not plate:
            print("❌ Error: License plate cannot be empty.")
            return

        make = input("Enter Make (optional, e.g. Tata, Hyundai) [Generic]: ").strip() or "Generic"
        model = input("Enter Model (optional, e.g. Nexon, Creta) [Car]: ").strip() or "Car"
        color = input("Enter Color (optional, e.g. White, Black) [Unknown]: ").strip() or "Unknown"
        floor_pref_str = input("Preferred Floor (1-12, press Enter for nearest): ").strip()

        preferred_floor = None
        if floor_pref_str.isdigit():
            val = int(floor_pref_str)
            if 1 <= val <= 12:
                preferred_floor = val

        result = self.lot.park_vehicle(
            license_plate=plate,
            make=make,
            model=model,
            color=color,
            preferred_floor=preferred_floor,
        )

        if result["status"] == "PARKED":
            ticket = result["ticket"]
            print("\n" + "┌" + "─" * 46 + "┐")
            print("│            PARKING TICKET ISSUED             │")
            print("├" + "─" * 46 + "┤")
            print(f"│ Ticket ID     : {ticket.ticket_id:<28} │")
            print(f"│ Vehicle Plate : {ticket.license_plate:<28} │")
            print(f"│ Vehicle Info  : {color} {make} {model}"[:46].ljust(47) + "│")
            print(f"│ Floor Number  : Floor {ticket.floor:<22} │")
            print(f"│ Spot ID       : {ticket.spot_id:<28} │")
            print(f"│ Entry Time    : {ticket.entry_time.strftime('%Y-%m-%d %H:%M:%S'):<28} │")
            print(f"│ Rate          : ₹{self.lot.fee_calculator.hourly_rate:.2f}/hr (1st 15m Free)"[:46].ljust(47) + "│")
            print("└" + "─" * 46 + "┘")
        elif result["status"] == "QUEUED":
            print("\n" + "!" * 54)
            print(" ⚠️  PARKING IS 100% FULL (All 600 spots occupied)!")
            print(f" Vehicle '{plate}' added to FIFO Waiting Queue.")
            print(f" Queue Position : #{result['queue_position']}")
            print(" As soon as any vehicle departs, this car will be")
            print(" automatically allocated a parking spot.")
            print("!" * 54)
        else:
            print(f"\n❌ {result['message']}")

    def handle_exit(self):
        print("\n--- [2] VEHICLE EXIT GATE & CHECKOUT (₹) ---")
        identifier = input("Enter License Plate or Ticket ID: ").strip()
        if not identifier:
            print("❌ Identifier cannot be empty.")
            return

        print("\nSelect Payment Method:")
        print("  1. UPI (GPay / PhonePe / Paytm / QR)")
        print("  2. FASTag (Automatic RFID Deduction)")
        print("  3. Cash (Rupee Currency Notes)")
        print("  4. Debit / Credit Card")
        method_choice = input("Choice (1-4) [default: 1 UPI]: ").strip()

        method_map = {
            "1": PaymentMethod.UPI,
            "2": PaymentMethod.FASTAG,
            "3": PaymentMethod.CASH,
            "4": PaymentMethod.CARD,
        }
        chosen_method = method_map.get(method_choice, PaymentMethod.UPI)

        result = self.lot.exit_vehicle(identifier, payment_method=chosen_method)

        if result["status"] == "SUCCESS":
            txn = result["transaction"]
            print("\n" + "╔" + "═" * 52 + "╗")
            print("║               OFFICIAL PAYMENT RECEIPT             ║")
            print("╠" + "═" * 52 + "╣")
            print(f"║ Transaction ID : {txn.txn_id:<32} ║")
            print(f"║ Ticket ID      : {txn.ticket_id:<32} ║")
            print(f"║ Vehicle Plate  : {txn.license_plate:<32} ║")
            print(f"║ Entry Time     : {txn.entry_time.strftime('%Y-%m-%d %H:%M:%S'):<32} ║")
            print(f"║ Exit Time      : {txn.exit_time.strftime('%Y-%m-%d %H:%M:%S'):<32} ║")
            print(f"║ Parked Duration: {result['duration_str']} ({result['duration_minutes']} minutes)"[:52].ljust(53) + "║")
            print("╟" + "─" * 52 + "╢")
            print(f"║ Total Amount   : {result['formatted_fee']:<32} ║")
            print(f"║ Payment Method : {txn.payment_method.value:<32} ║")
            print(f"║ Payment Status : PAID / SUCCESS                     ║")
            print("╚" + "═" * 52 + "╝")

            # Check if a queued car was auto-admitted
            if result.get("auto_admitted"):
                admitted = result["auto_admitted"]
                veh = admitted["vehicle"]
                tkt = admitted["ticket"]
                print("\n" + "★" * 54)
                print(" 🔔 AUTO-ADMISSION FROM WAITING QUEUE:")
                print(f" Waiting car '{veh.license_plate}' ({veh.color} {veh.make} {veh.model})")
                print(f" has been automatically assigned Spot {tkt.spot_id} on Floor {tkt.floor}!")
                print(f" New Ticket ID: {tkt.ticket_id}")
                print("★" * 54)
        else:
            print(f"\n❌ {result['message']}")

    def handle_search(self):
        print("\n--- [3] SEARCH VEHICLE LOCATION ---")
        plate = input("Enter License Plate to search: ").strip()
        if not plate:
            print("❌ Plate cannot be empty.")
            return

        res = self.lot.find_vehicle(plate)
        if res["status"] == "PARKED":
            print("\n" + "─" * 46)
            print(f" ✅ VEHICLE FOUND (PARKED)")
            print(f" Plate Number    : {res['license_plate']}")
            print(f" Location        : Floor {res['floor']}, Spot #{res['spot_number']} ({res['spot_id']})")
            print(f" Ticket ID       : {res['ticket_id']}")
            print(f" Entry Time      : {res['entry_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f" Parked Duration : {res['current_duration']}")
            print(f" Accrued Fee (₹) : {res['accrued_fee']}")
            print("─" * 46)
        elif res["status"] == "QUEUED":
            print("\n" + "─" * 46)
            print(f" ⏳ VEHICLE IS IN WAITING QUEUE")
            print(f" Plate Number    : {res['license_plate']}")
            print(f" Queue Position  : #{res['queue_position']} of {res['total_waiting']}")
            print(f" Time Waiting    : {res['wait_minutes']} minutes")
            print("─" * 46)
        else:
            print(f"\n❌ {res['message']}")

    def handle_floors_dashboard(self):
        print("\n--- [4] 12-FLOOR REAL-TIME OCCUPANCY DASHBOARD ---")
        floors_data = self.lot.get_floor_occupancy()
        print(f"{'Floor':<10} | {'Occupancy Bar':<22} | {'Occupied':<10} | {'Available':<10} | {'Status'}")
        print("─" * 68)

        for fd in floors_data:
            fnum = fd["floor"]
            occ = fd["occupied"]
            cap = fd["capacity"]
            free = fd["free"]
            pct = fd["percentage"]
            bar = _render_progress_bar(occ, cap, 18)
            status = "🔴 FULL" if free == 0 else ("🟡 BUSY" if pct >= 80 else "🟢 OPEN")
            print(f"Floor {fnum:02d}   | {bar} | {occ:>2}/{cap} ({pct:>5.1f}%) | {free:>2} spots   | {status}")
        print("─" * 68)

    def handle_floor_grid(self):
        print("\n--- [5] FLOOR SPOT GRID MAP (50 SPOTS) ---")
        f_str = input("Enter Floor Number (1-12): ").strip()
        if not f_str.isdigit() or not (1 <= int(f_str) <= 12):
            print("❌ Invalid floor number. Must be between 1 and 12.")
            return

        fnum = int(f_str)
        floor = self.lot.floors[fnum]
        print(f"\nFloor {fnum:02d} Layout: 50 Spots (Occupied: {floor.occupied_count}/50, Free: {floor.free_count}/50)")
        print("Legend: [🟢 S01: OPEN ] = Vacant spot | [🔴 S01:MH12AB] = Occupied spot")
        print("═" * 78)

        # Print in 5 rows of 10 spots
        for row in range(5):
            row_spots = []
            for col in range(1, 11):
                snum = row * 10 + col
                spot = floor.get_spot(snum)
                if spot and spot.is_occupied and spot.current_vehicle:
                    plate_snippet = spot.current_vehicle.license_plate[:6]
                    row_spots.append(f"[🔴 {snum:02d}:{plate_snippet:<6}]")
                else:
                    row_spots.append(f"[🟢 {snum:02d}:OPEN  ]")
            print(" ".join(row_spots))
        print("═" * 78)

    def handle_waiting_queue(self):
        print("\n--- [6] WAITING QUEUE STATUS ---")
        items = self.lot.waiting_queue.list_waiting()
        if not items:
            print("ℹ️ The waiting queue is currently empty. Parking spots are available.")
            return

        print(f"Total Vehicles in Queue: {len(items)}")
        print(f"{'Pos':<4} | {'License Plate':<14} | {'Vehicle Details':<22} | {'Wait Time':<10} | {'Pref Floor'}")
        print("─" * 68)
        for item in items:
            pref = f"Floor {item['preferred_floor']}" if item["preferred_floor"] else "Any"
            veh_info = f"{item['color']} {item['make']} {item['model']}"[:20]
            print(f"#{item['position']:<3} | {item['license_plate']:<14} | {veh_info:<22} | {item['wait_minutes']} mins    | {pref}")
        print("─" * 68)

    def handle_transactions(self):
        print("\n--- [7] TRANSACTION HISTORY & REVENUE (₹) ---")
        txns = self.lot.transactions
        if not txns:
            print("ℹ️ No transactions recorded yet.")
            return

        total_rev = self.lot.total_revenue_inr
        print(f"Total Transactions : {len(txns)}")
        print(f"Total Revenue (₹)  : {self.lot.fee_calculator.format_inr(total_rev)}")
        print("─" * 84)
        print(f"{'Txn ID':<14} | {'Plate':<12} | {'Duration':<9} | {'Amount (₹)':<12} | {'Method':<8} | {'Timestamp'}")
        print("─" * 84)

        for txn in reversed(txns[-15:]):  # show last 15
            amount_str = self.lot.fee_calculator.format_inr(txn.amount_inr)
            ts = txn.timestamp.strftime("%Y-%m-%d %H:%M")
            dur = f"{txn.duration_minutes}m"
            print(f"{txn.txn_id:<14} | {txn.license_plate:<12} | {dur:<9} | {amount_str:<12} | {txn.payment_method.value:<8} | {ts}")

        if len(txns) > 15:
            print(f"... and {len(txns) - 15} earlier transactions.")
        print("─" * 84)

    def handle_simulation(self):
        print("\n--- [8] SIMULATION / LOAD GENERATOR ---")
        print("  1. Fill Garage to 595 cars (Leaves 5 open spots to quickly test filling & queue)")
        print("  2. Fill Garage to 100% capacity (600 cars) and queue 3 cars")
        print("  3. Park 10 random vehicles")
        print("  4. Simulate 5 random departures (processes ₹ payments & queue discharges)")
        sim_choice = input("Select simulation action (1-4): ").strip()

        if sim_choice == "1":
            added = prefill_parking_lot(self.lot, count=595)
            print(f"✅ Added {added} vehicles! Total parked: {self.lot.total_occupied}/600.")
        elif sim_choice == "2":
            added = prefill_parking_lot(self.lot, count=600)
            print(f"✅ Filled garage to 600/600 spots!")
            # Add 3 queued vehicles
            for i in range(1, 4):
                veh = generate_random_vehicle()
                res = self.lot.park_vehicle(veh.license_plate, veh.make, veh.model, veh.color)
                print(f"   Queued: {veh.license_plate} -> {res['message']}")
        elif sim_choice == "3":
            count = 0
            for _ in range(10):
                veh = generate_random_vehicle()
                res = self.lot.park_vehicle(veh.license_plate, veh.make, veh.model, veh.color)
                if res["status"] in ("PARKED", "QUEUED"):
                    count += 1
            print(f"✅ Processed 10 random arrivals ({count} successful).")
        elif sim_choice == "4":
            if not self.lot.active_tickets_by_plate:
                print("❌ No parked vehicles to depart.")
                return
            plates = list(self.lot.active_tickets_by_plate.keys())[:5]
            for plate in plates:
                res = self.lot.exit_vehicle(plate, payment_method=PaymentMethod.UPI)
                print(f"   Departed: {plate} -> Paid: {res['formatted_fee']} ({res['duration_str']})")
                if res.get("auto_admitted"):
                    adm = res["auto_admitted"]
                    print(f"   ↪ Auto-admitted queued car {adm['vehicle'].license_plate} to {adm['spot_id']}")
        else:
            print("❌ Invalid option.")

    def handle_storage(self):
        print("\n--- [9] SAVE / LOAD STATE (JSON) ---")
        print("  1. Save current state to 'parking_state.json'")
        print("  2. Load state from 'parking_state.json'")
        choice = input("Choice (1 or 2): ").strip()

        if choice == "1":
            path = ParkingStorage.save_to_file(self.lot)
            print(f"✅ State successfully saved to '{path}'.")
        elif choice == "2":
            try:
                self.lot = ParkingStorage.load_from_file()
                print("✅ State successfully loaded from 'parking_state.json'.")
            except Exception as e:
                print(f"❌ Failed to load state: {e}")
        else:
            print("❌ Invalid option.")

    def run(self):
        """Main interaction loop."""
        while True:
            self.print_header()
            self.print_menu()
            choice = input("Enter option [0-9]: ").strip()

            if choice == "1":
                self.handle_park()
            elif choice == "2":
                self.handle_exit()
            elif choice == "3":
                self.handle_search()
            elif choice == "4":
                self.handle_floors_dashboard()
            elif choice == "5":
                self.handle_floor_grid()
            elif choice == "6":
                self.handle_waiting_queue()
            elif choice == "7":
                self.handle_transactions()
            elif choice == "8":
                self.handle_simulation()
            elif choice == "9":
                self.handle_storage()
            elif choice == "0":
                print("\n👋 Exiting Car Parking & Queue System. Have a wonderful day!\n")
                break
            else:
                print("\n❌ Invalid choice, please choose an option between 0 and 9.")
            
            input("\nPress [Enter] to continue...")
