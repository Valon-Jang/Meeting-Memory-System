import json
import tempfile
import unittest
from pathlib import Path

from meeting_memory_system.engine import ingest_payload, meeting_record, next_meeting_brief, person_card
from meeting_memory_system.store import MeetingMemoryStore

EXAMPLE = Path(__file__).parents[1] / "examples" / "synthetic_meeting.json"


class MeetingMemorySystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MeetingMemoryStore(Path(self.tmp.name) / "memory.db")
        self.payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        ingest_payload(self.store, self.payload)

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def test_ingest_is_idempotent(self):
        ingest_payload(self.store, self.payload)
        self.assertEqual(self.store.row("SELECT COUNT(*) AS n FROM conversation_item")["n"], 5)

    def test_person_card_prioritizes_facilitator_to_person(self):
        self.assertEqual(person_card(self.store, "P-MINA")["facilitator_to_person"][0]["item_id"], "I-002")

    def test_low_confidence_candidate_not_in_long_term_memory(self):
        card = person_card(self.store, "P-MINA")
        self.assertNotIn("I-005", {x["item_id"] for x in card["timeline"]})
        self.assertIn("I-005", {x["item_id"] for x in card["review_queue"]})

    def test_next_meeting_brief_contains_open_commitment(self):
        ids = {x["item_id"] for x in next_meeting_brief(self.store, "P-MINA", "2026-09-03")["open_commitments_and_requests"]}
        self.assertIn("I-002", ids); self.assertIn("I-003", ids)

    def test_overdue_is_derived_from_due_date(self):
        ids = {x["item_id"] for x in next_meeting_brief(self.store, "P-MINA", "2026-09-03")["overdue"]}
        self.assertIn("I-002", ids)

    def test_meeting_record_preserves_evidence_links(self):
        record = meeting_record(self.store, "M-20260830-001")
        item = next(x for x in record["conversation_items"] if x["item_id"] == "I-002")
        self.assertEqual(item["evidence_utterance_ids"], ["U-002"])

    def test_unknown_evidence_is_rejected(self):
        bad = json.loads(json.dumps(self.payload))
        bad["meeting"]["meeting_id"] = "M-BAD"
        bad["conversation_items"][0]["item_id"] = "I-BAD"
        bad["conversation_items"][0]["evidence_utterance_ids"] = ["U-NOT-THERE"]
        with self.assertRaises(ValueError): ingest_payload(self.store, bad)


if __name__ == "__main__": unittest.main()
