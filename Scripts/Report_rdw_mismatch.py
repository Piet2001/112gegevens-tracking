import json
import os

REPORT_TARGETS = [
    {
        "name": "brandweer",
        "source_json_file": "Brandweer.json",
        "source_rdw_file": os.path.join("Data", "Brandweer_rdw.json"),
        "report_json_file": os.path.join("Data", "Report_brandweer_rdw_not_in_brandweer_json.json"),
        "report_txt_file": os.path.join("Data", "Report_brandweer_rdw_not_in_brandweer_json.txt"),
        "json_kenteken_key": "Kenteken",
    },
    {
        "name": "ambulance",
        "source_json_file": "Ambulance.json",
        "source_rdw_file": os.path.join("Data", "Ambulance_rdw.json"),
        "report_json_file": os.path.join("Data", "Report_ambulance_rdw_not_in_ambulance_json.json"),
        "report_txt_file": os.path.join("Data", "Report_ambulance_rdw_not_in_ambulance_json.txt"),
        "json_kenteken_key": "Kenteken",
    },
]


def normalize_kenteken(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.upper() if ch.isalnum())


def load_source_kentekens(source_json_file: str, kenteken_key: str) -> set[str]:
    with open(source_json_file, encoding="utf-8") as f:
        data = json.load(f)

    placeholders = {"", "GEEN", "ONBEKEND", "-"}
    result = set()
    for item in data:
        raw = (item.get(kenteken_key) or "").strip().upper()
        if raw in placeholders:
            continue
        norm = normalize_kenteken(raw)
        if norm:
            result.add(norm)

    return result


def load_rdw_kentekens(source_rdw_file: str) -> set[str]:
    with open(source_rdw_file, encoding="utf-8") as f:
        data = json.load(f)

    result = set()
    for item in data:
        norm = normalize_kenteken(item.get("kenteken"))
        if norm:
            result.add(norm)

    return result


def write_reports(
    source_json_file: str,
    source_rdw_file: str,
    report_json_file: str,
    report_txt_file: str,
    rdw_not_in_source: list[str],
) -> None:
    json_payload = {
        "source_json_file": source_json_file,
        "source_rdw_file": source_rdw_file,
        "rdw_not_in_source_count": len(rdw_not_in_source),
        "rdw_not_in_source_kentekens": rdw_not_in_source,
    }

    with open(report_json_file, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)

    source_name = os.path.basename(source_json_file)
    with open(report_txt_file, "w", encoding="utf-8") as f:
        f.write(f"Report: vergelijking {source_name} met RDW-lijst\n")
        f.write(f"RDW wel, {source_name} niet ({len(rdw_not_in_source)}):\n")
        for kenteken in rdw_not_in_source:
            f.write(kenteken + "\n")


def generate_report_for_target(target: dict[str, str]) -> dict[str, int | str]:
    source_json_file = target["source_json_file"]
    source_rdw_file = target["source_rdw_file"]
    report_json_file = target["report_json_file"]
    report_txt_file = target["report_txt_file"]
    kenteken_key = target["json_kenteken_key"]
    name = target["name"]

    source_kentekens = load_source_kentekens(source_json_file, kenteken_key)
    rdw_kentekens = load_rdw_kentekens(source_rdw_file)

    rdw_not_in_source = sorted(rdw_kentekens - source_kentekens)
    write_reports(
        source_json_file,
        source_rdw_file,
        report_json_file,
        report_txt_file,
        rdw_not_in_source,
    )

    print(f"[{name}] Klaar. {len(rdw_not_in_source)} kentekens in RDW maar niet in {source_json_file}")
    print(f"[{name}] JSON report: {report_json_file}")
    print(f"[{name}] TXT report: {report_txt_file}")

    return {
        "name": name,
        "rdw_not_in_source_count": len(rdw_not_in_source),
    }


def generate_all_reports() -> list[dict[str, int | str]]:
    results: list[dict[str, int | str]] = []
    for target in REPORT_TARGETS:
        results.append(generate_report_for_target(target))
    return results


def main() -> None:
    generate_all_reports()


if __name__ == "__main__":
    main()