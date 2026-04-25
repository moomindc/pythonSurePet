import sys
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
import requests
from tabulate import tabulate

import json 

BASE_URL = "https://app-api.production.surehub.io"

LOCK_MODE_LABELS = {0: "NONE", 1: "IN ONLY", 2: "OUT ONLY", 3: "BOTH"}
PET_WHERE_LABELS = {0: "UNKNOWN", 1: "INSIDE", 2: "OUTSIDE"}

# product_id 6 = DUALSCAN_CAT_FLAP_CONNECT, 9 = CAT_FLAP_CONNECT
CAT_FLAP_PRODUCT_IDS = {6, 9}


def load_credentials():
    load_dotenv()
    email = os.getenv("SUREPET_EMAIL")
    password = os.getenv("SUREPET_PASSWORD")
    if not email or not password:
        print("ERROR: SUREPET_EMAIL and SUREPET_PASSWORD must be set in .env or environment.")
        sys.exit(1)
    return email, password


def make_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "https://surehub.io",
    }


def login(email, password):
    url = f"{BASE_URL}/api/auth/login"
    payload = {"device_id": "web", "email_address": email, "password": password}
    try:
        resp = requests.post(url, json=payload, timeout=15)
    except requests.ConnectionError:
        print("ERROR: Cannot reach SurePet API. Check your internet connection.")
        sys.exit(1)
    except requests.Timeout:
        print("ERROR: Request timed out connecting to SurePet API.")
        sys.exit(1)

    if resp.status_code in (401, 403):
        print("ERROR: Invalid credentials. Check SUREPET_EMAIL and SUREPET_PASSWORD.")
        sys.exit(1)
    if not resp.ok:
        print(f"ERROR: Login failed (HTTP {resp.status_code}): {resp.text[:200]}")
        sys.exit(1)

    return resp.json()["data"]["token"]


def fetch_start_data(token):
    url = f"{BASE_URL}/api/me/start"
    try:
        resp = requests.get(url, headers=make_headers(token), timeout=15)
    except requests.ConnectionError:
        print("ERROR: Cannot reach SurePet API. Check your internet connection.")
        sys.exit(1)
    except requests.Timeout:
        print("ERROR: Request timed out fetching data.")
        sys.exit(1)

    if not resp.ok:
        print(f"ERROR: Failed to fetch data (HTTP {resp.status_code}).")
        sys.exit(1)

    return resp.json()["data"]


def get_cat_flaps(data):
    devices = data.get("devices", [])
    flaps = [d for d in devices if d.get("product_id") in CAT_FLAP_PRODUCT_IDS]
    if not flaps:
        # Fallback: any device that has a curfew control setting
        flaps = [d for d in devices if d.get("control", {}).get("curfew") is not None]
    return flaps


def format_curfew(curfew_raw):
    if curfew_raw is None:
        return "N/A"

    # API may return a list of curfew entries or a single object
    if isinstance(curfew_raw, list):
        if not curfew_raw:
            return "N/A"
        # Prefer the first enabled entry, otherwise the first entry
        entry = next((c for c in curfew_raw if c.get("enabled")), curfew_raw[0])
    else:
        entry = curfew_raw

    enabled = entry.get("enabled", False)
    if not enabled:
        return "Disabled"

    lock_time = entry.get("lock_time", "")[:5]    # trim seconds if present
    unlock_time = entry.get("unlock_time", "")[:5]
    return f"Enabled ({lock_time} \u2013 {unlock_time})"


def display_device_info(devices):
    print("=== Cat Flap Devices ===")
    if not devices:
        print("No cat flap devices found.")
        return

    rows = []
    for d in devices:
        name = d.get("name", f"Device {d.get('id', '?')}")
        control = d.get("control") or {}
        status = d.get("status") or {}

        curfew_str = format_curfew(control.get("curfew"))
        locking = control.get("locking")
        lock_str = LOCK_MODE_LABELS.get(locking, "N/A") if locking is not None else "N/A"

        battery = status.get("battery")
        rows.append((name, curfew_str, lock_str, battery))

    # Include battery column only if at least one device has a value
    has_battery = any(r[3] is not None for r in rows)
    if has_battery:
        headers = ["Device", "Curfew", "Lock Mode", "Battery"]
        table = [(r[0], r[1], r[2], r[3] if r[3] is not None else "N/A") for r in rows]
    else:
        headers = ["Device", "Curfew", "Lock Mode"]
        table = [(r[0], r[1], r[2]) for r in rows]

    print(tabulate(table, headers=headers))


def display_pet_list(data):
    print("=== Pet Status ===")
    pets = data.get("pets", [])
    if not pets:
        print("No pets found.")
        return

    rows = []
    for pet in sorted(pets, key=lambda p: p.get("name", "").lower()):
        name = pet.get("name", f"Pet {pet.get('id', '?')}")
        where = (pet.get("position") or {}).get("where", 0)
        location = PET_WHERE_LABELS.get(where, "UNKNOWN")
        rows.append((name, location))

    print(tabulate(rows, headers=["Name", "Location"]))


def toggle_pet(data, token, name):
    pets = data.get("pets", [])
    pet = next((p for p in pets if p.get("name", "").lower() == name.lower()), None)

    if pet is None:
        available = ", ".join(p.get("name", "?") for p in pets)
        print(f"ERROR: No pet named '{name}' found. Available pets: {available}")
        sys.exit(1)

    current_where = (pet.get("position") or {}).get("where", 0)
    # UNKNOWN (0) is treated as OUTSIDE; toggle → INSIDE
    new_where = 2 if current_where == 1 else 1

    payload = {
        "where": new_where,
        "since": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    pet_id = pet["id"]
    url = f"{BASE_URL}/api/pet/{pet_id}/position"
    try:
        resp = requests.post(url, json=payload, headers=make_headers(token), timeout=15)
    except (requests.ConnectionError, requests.Timeout) as e:
        print(f"ERROR: Network error updating pet position: {e}")
        sys.exit(1)

    if resp.status_code == 404:
        print(f"ERROR: Pet ID {pet_id} not found on the server.")
        sys.exit(1)
    if not resp.ok:
        print(f"ERROR: Failed to update pet position (HTTP {resp.status_code}).")
        sys.exit(1)

    display_name = pet.get("name", name)
    print(f"OK: {display_name} is now {PET_WHERE_LABELS[new_where]}.")


def print_usage():
    print("Usage:")
    print("  python surepet.py [status]       Show device info and pet status")
    print("  python surepet.py toggle <name>  Toggle pet inside/outside")


def main():
    args = sys.argv[1:]

    command = args[0] if args else "status"

    if command not in ("status", "toggle"):
        print_usage()
        sys.exit(1)

    email, password = load_credentials()
    token = login(email, password)
    data = fetch_start_data(token)
    #DRC Debug
    #json_formatted_str = json.dumps(data, indent=4)
    print(json_formatted_str)
    

    if command == "status":
        cat_flaps = get_cat_flaps(data)
        display_device_info(cat_flaps)
        print()
        display_pet_list(data)

    elif command == "toggle":
        if len(args) < 2:
            print("ERROR: 'toggle' requires a pet name. E.g.: python surepet.py toggle Mochi")
            print_usage()
            sys.exit(1)
        toggle_pet(data, token, args[1])


if __name__ == "__main__":
    main()
