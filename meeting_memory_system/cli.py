from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import ingest_payload, load_payload, meeting_record, next_meeting_brief, person_card
from .store import MeetingMemoryStore


def _print(value, pretty: bool) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2 if pretty else None, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="meeting-memory", description="Persistent structured meeting memory")
    parser.add_argument("--db", default="meeting_memory.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Ingest one structured meeting JSON file")
    ingest.add_argument("input", type=Path); ingest.add_argument("--pretty", action="store_true")
    card = sub.add_parser("person", help="Render a person memory card")
    card.add_argument("person_id"); card.add_argument("--pretty", action="store_true")
    brief = sub.add_parser("brief", help="Generate a next-meeting brief")
    brief.add_argument("person_id"); brief.add_argument("--as-of"); brief.add_argument("--pretty", action="store_true")
    meeting = sub.add_parser("meeting", help="Render a complete meeting record")
    meeting.add_argument("meeting_id"); meeting.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with MeetingMemoryStore(args.db) as store:
        if args.command == "ingest": result = ingest_payload(store, load_payload(args.input))
        elif args.command == "person": result = person_card(store, args.person_id)
        elif args.command == "brief": result = next_meeting_brief(store, args.person_id, args.as_of)
        else: result = meeting_record(store, args.meeting_id)
    _print(result, args.pretty)
    return 0
