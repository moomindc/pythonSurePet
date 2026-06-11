# SurePet CLI

A command-line tool for monitoring and controlling [Sure Petcare](https://www.surepetcare.com/) smart cat flaps and tracking pet locations.

## What it does

- Displays cat flap device status: curfew schedule, lock mode, and battery level
- Shows where each pet is (inside or outside)
- Toggles a pet's recorded location between inside and outside

## How it works

The script authenticates against the unofficial Sure Petcare API (`app-api.production.surehub.io`) using your account email and password, retrieves device and pet data, and presents it in formatted tables. It targets devices with product IDs for the **DualScan Cat Flap Connect** (product 6) and **Cat Flap Connect** (product 9).

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP calls to the Sure Petcare API |
| `python-dotenv` | Loads credentials from a `.env` file |
| `tabulate` | Formats output as aligned tables |

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> If you get an execution policy error, run this once first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure credentials

Copy `.env.example` to `.env` and fill in your Sure Petcare account details:

```
SUREPET_EMAIL=your@email.com
SUREPET_PASSWORD=yourpassword
```

## Usage

```powershell
# Show cat flap status and pet locations (default)
python surepet.py
python surepet.py status

# Toggle a pet's location between inside and outside
python surepet.py toggle <PetName>
```

### Example output

```
=== Cat Flap Devices ===
Device          Curfew                    Lock Mode    Battery
--------------  ------------------------  -----------  ---------
Cat Flap        Enabled (22:00 – 07:00)  NONE         3.14

=== Pet Status ===
Name      Location
--------  --------
Mochi     INSIDE
Shadow    OUTSIDE
```

## Deactivating the virtual environment

```powershell
deactivate
```
