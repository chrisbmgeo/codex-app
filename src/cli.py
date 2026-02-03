#!/usr/bin/env python3
"""Simple CLI for recording shift-related dates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "shifts.json"

QUESTIONS = [
    ("service", "Πότε θα κάνεις υπηρεσία;"),
    ("presence", "Πότε θα κάνεις παρουσία;"),
    ("leave", "Πότε θα πάρεις κενό;"),
]


def load_entries() -> List[Dict[str, str]]:
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_entries(entries: List[Dict[str, str]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)


def prompt_entries() -> None:
    entries = load_entries()
    timestamp = datetime.now().isoformat(timespec="seconds")
    for entry_type, question in QUESTIONS:
        answer = input(f"{question} ").strip()
        if not answer:
            continue
        entries.append(
            {
                "date": answer,
                "type": entry_type,
                "recorded_at": timestamp,
            }
        )
    save_entries(entries)
    print("Οι καταχωρήσεις αποθηκεύτηκαν στο data/shifts.json")


def list_entries() -> None:
    entries = load_entries()
    if not entries:
        print("Δεν υπάρχουν καταχωρήσεις ακόμα.")
        return
    print("Καταχωρήσεις:")
    for entry in entries:
        entry_type = entry.get("type", "-")
        date_value = entry.get("date", "-")
        recorded_at = entry.get("recorded_at", "-")
        print(f"- {entry_type}: {date_value} (καταγράφηκε {recorded_at})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Καταγραφή υπηρεσίας/παρουσίας/κενού σε JSON."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("prompt", help="Εμφανίζει τις ερωτήσεις καταχώρησης.")
    subparsers.add_parser("list", help="Εμφανίζει τις αποθηκευμένες καταχωρήσεις.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "prompt"):
        prompt_entries()
        return

    if args.command == "list":
        list_entries()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
