import requests
import json
from datetime import datetime
import time
import os
from Functions import discord

KENTEKEN_STATUS_FILE = "apk_kenteken_status.json"
REPORT_FILE = "apk_expiry_report.txt"

# 1. Collect all kentekens from the relevant JSON files
def collect_kentekens_with_roepnummer():
    kenteken_map = {}
    # Brandweer.json
    with open('Brandweer.json', encoding='utf-8') as f:
        data = json.load(f)
        for entry in data:
            kenteken = entry.get('Kenteken')
            roep = entry.get('Roepnummer')
            if kenteken and kenteken not in ['GEEN', 'ONBEKEND', '-']:
                kenteken_map.setdefault(kenteken, set()).add(roep)
    # Ambulance.json
    with open('Ambulance.json', encoding='utf-8') as f:
        data = json.load(f)
        for entry in data:
            kenteken = entry.get('Kenteken')
            roep = entry.get('Roepnummer')
            if kenteken and kenteken not in ['GEEN', 'ONBEKEND', '-']:
                kenteken_map.setdefault(kenteken, set()).add(roep)
    # Convert sets to sorted lists and remove None
    kenteken_map = {k: sorted([r for r in v if r]) for k, v in kenteken_map.items()}
    return kenteken_map

# 2. Load or initialize kenteken status file
def load_kenteken_status(kenteken_map):
    if os.path.exists(KENTEKEN_STATUS_FILE):
        with open(KENTEKEN_STATUS_FILE, encoding='utf-8') as f:
            status = json.load(f)
    else:
        status = {}
    original_status = {k: v.copy() for k, v in status.items()}
    removed_kentekens = []
    added_kentekens = []
    # Remove kentekens that are no longer in the lists
    to_remove = [k for k in status if k not in kenteken_map]
    for k in to_remove:
        removed_kentekens.append({"kenteken": k, "roepnummers": status[k].get("roepnummers", [])})
        del status[k]
    # Ensure all kentekens are present and update roepnummers
    for k, roepnummers in kenteken_map.items():
        if k not in status:
            status[k] = {"expiry": None, "checked": False, "unknown": True, "roepnummers": roepnummers, "last_check_date": None}
            added_kentekens.append({"kenteken": k, "roepnummers": roepnummers})
        else:
            # Always update roepnummers for completeness
            status[k]["roepnummers"] = roepnummers
            if "last_check_date" not in status[k]:
                status[k]["last_check_date"] = None
    if not original_status:
        # On first run, do not send notifications for all existing kentekens.
        return status, [], []
    return status, added_kentekens, removed_kentekens

def save_kenteken_status(status):
    with open(KENTEKEN_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

# 3. Collect APK info from RDW Open Data API
def get_apk_info(kenteken):
    url = f'https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={kenteken.replace("-", "").upper()}'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]  # Return first result
    except Exception as e:
        print(f"Fout bij ophalen APK info voor {kenteken}: {e}")
    return None

# 4. Check if APK is valid
def is_apk_valid(apk_info):
    vervaldatum = apk_info.get('vervaldatum_apk')
    if vervaldatum:
        expiry = datetime.strptime(vervaldatum, '%Y%m%d').date()
        return expiry >= datetime.today().date(), expiry
    return False, None

# 5. Main script
def main():
    kenteken_map = collect_kentekens_with_roepnummer()
    status, added_kentekens, removed_kentekens = load_kenteken_status(kenteken_map)

    for item in added_kentekens:
        roepnummers = item.get("roepnummers", [])
        roep_str = f" ({', '.join(roepnummers)})" if roepnummers else ""
        msg = f"Kenteken added: {item['kenteken']}{roep_str}"
        print(f"  {msg}")
        discord.webhook_APK_LOG(msg)
        time.sleep(10)

    for item in removed_kentekens:
        roepnummers = item.get("roepnummers", [])
        roep_str = f" ({', '.join(roepnummers)})" if roepnummers else ""
        msg = f"Kenteken removed: {item['kenteken']}{roep_str}"
        print(f"  {msg}")
        discord.webhook_APK_LOG(msg)
        time.sleep(10)

    # Prioritize unknown, then expired, then others
    today = datetime.today().date()
    week_ago = today.fromordinal(today.toordinal() - 7)
    # Check all unknown kentekens (never checked or not checked in 7+ days)
    unknowns = [k for k, v in status.items() if v["unknown"] and (not v.get("last_check_date") or datetime.strptime(v["last_check_date"], "%Y-%m-%d").date() <= week_ago)]
    # Check all expired kentekens, but only if not checked today
    expired = [
        k for k, v in status.items()
        if v["expiry"] and v["expiry"] not in [None, "None", "null", ""]
        and datetime.strptime(v["expiry"], "%Y-%m-%d").date() < today
        and (
            not v.get("last_check_date")
            or datetime.strptime(v["last_check_date"], "%Y-%m-%d").date() < today
        )
    ]
    # Combine and deduplicate
    to_check = list(dict.fromkeys(unknowns + expired))
    # Limit to max 1000 per run
    if len(to_check) > 1000:
        print(f"Let op: er zijn {len(to_check)} kentekens om te checken, maar maximaal 1000 worden nu verwerkt.")
        to_check = to_check[:1000]
    output_lines = []
    print(f"Start batch check van {len(to_check)} kentekens...")
    for idx, kenteken in enumerate(to_check, 1):
        print(f"[{idx}/{len(to_check)}] Check {kenteken}...")
        apk_info = get_apk_info(kenteken)
        status[kenteken]["last_check_date"] = today.strftime("%Y-%m-%d")
        if not apk_info:
            print(f"  Geen APK info gevonden voor {kenteken}")
            status[kenteken]["expiry"] = None
            status[kenteken]["checked"] = True
            status[kenteken]["unknown"] = True
            continue
        valid, expiry = is_apk_valid(apk_info)
        previous_expiry = status[kenteken].get("expiry")
        status[kenteken]["expiry"] = str(expiry)
        status[kenteken]["checked"] = True
        # If expiry is None, treat as unknown, not expired
        if expiry is None:
            status[kenteken]["unknown"] = True
            print(f"  {kenteken}: APK vervaldatum onbekend")
        else:
            status[kenteken]["unknown"] = False
            roepnummers = status[kenteken].get("roepnummers", [])
            roep_str = f" ({', '.join(roepnummers)})" if roepnummers else ""
            # Check if previously expired and now valid (verlengt)
            verlengt = False
            if previous_expiry not in [None, "None", "null", ""]:
                try:
                    prev_expiry_date = datetime.strptime(previous_expiry, "%Y-%m-%d").date()
                    if prev_expiry_date < today and valid:
                        verlengt = True
                except Exception:
                    pass
            if verlengt:
                print(f"  {kenteken}: APK verlengt tot {expiry}")
                msg = f"{kenteken}{roep_str}: APK verlengt tot {expiry}"
                discord.webhook_APK(msg)
                time.sleep(10)
            elif not valid:
                print(f"  {kenteken}: verlopen op {expiry}")
                # Only send Discord message if expiry was a week or more ago
                if expiry <= today.fromordinal(today.toordinal() - 7):
                    msg = f"{kenteken}{roep_str}: APK verlopen op {expiry}"
                    discord.webhook_APK(msg)
                    time.sleep(10)
            else:
                print(f"  {kenteken}: APK geldig tot {expiry}")
    save_kenteken_status(status)

    # Always write a fresh, deduplicated, up-to-date report, excluding unchecked kentekens
    expired_lines = []
    unknown_lines = []
    for kenteken, v in status.items():
        if not v.get("checked", False):
            continue  # Skip unchecked kentekens
        roepnummers = v.get("roepnummers", [])
        roep_str = f" ({', '.join(roepnummers)})" if roepnummers else ""
        if v["unknown"] or v["expiry"] in [None, "None", "null", ""]:
            unknown_lines.append(f"{kenteken}{roep_str}")
        else:
            try:
                expiry_date = datetime.strptime(v["expiry"], "%Y-%m-%d").date()
                if expiry_date < today:
                    expired_lines.append(f"{kenteken}{roep_str}: verlopen op {v['expiry']}")
            except Exception:
                expired_lines.append(f"{kenteken}{roep_str}: verlopen op {v['expiry']}")
    # Remove duplicates and sort
    expired_lines = sorted(set(expired_lines))
    unknown_lines = sorted(set(unknown_lines))
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Expired ({len(expired_lines)}):\n")
        for line in expired_lines:
            f.write(line + "\n")
        f.write(f"\nUnknown ({len(unknown_lines)}):\n")
        for line in unknown_lines:
            f.write(line + "\n")
    print(f"Rapport bijgewerkt in {REPORT_FILE}")

if __name__ == "__main__":
    main()
