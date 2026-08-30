from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .models import ConversationItem, Meeting, Person, Utterance
from .store import MeetingMemoryStore

OPEN_TYPES = {"REQUEST", "PROMISE", "INSTRUCTION", "OPEN_ITEM", "QUESTION"}
AGREEMENT_TYPES = {"DECISION", "PROMISE", "REQUEST"}
FACT_TYPES = {"FACT", "INTEREST", "POSITION", "PERSONAL_FACT"}


def _dict_row(row) -> dict[str, Any]:
    result = dict(row)
    for key in ("evidence_utterance_ids_json", "addressee_person_ids_json"):
        if key in result:
            result[key.removesuffix("_json")] = json.loads(result.pop(key))
    return result


def load_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ingest_payload(store: MeetingMemoryStore, payload: dict[str, Any]) -> dict[str, Any]:
    people = [Person.from_dict(x) for x in payload.get("people", [])]
    meeting = Meeting.from_dict(payload["meeting"])
    participant_ids = [str(x) for x in payload.get("participant_ids", [])]
    utterances = [Utterance.from_dict(meeting.meeting_id, x) for x in payload.get("utterances", [])]
    items = [ConversationItem.from_dict(meeting.meeting_id, x) for x in payload.get("conversation_items", [])]
    person_ids = {p.person_id for p in people}
    if meeting.facilitator_person_id and meeting.facilitator_person_id not in person_ids:
        raise ValueError("facilitator_person_id must exist in people")
    missing_participants = set(participant_ids) - person_ids
    if missing_participants:
        raise ValueError(f"unknown participant ids: {sorted(missing_participants)}")
    utterance_ids = {u.utterance_id for u in utterances}
    if len(utterance_ids) != len(utterances):
        raise ValueError("duplicate utterance_id in payload")
    item_ids = {i.item_id for i in items}
    if len(item_ids) != len(items):
        raise ValueError("duplicate item_id in payload")
    missing_evidence = sorted({e for i in items for e in i.evidence_utterance_ids if e not in utterance_ids})
    if missing_evidence:
        raise ValueError(f"conversation item references unknown utterances: {missing_evidence}")
    store.ingest(people, meeting, participant_ids, utterances, items)
    return {"meeting_id":meeting.meeting_id,"people":len(people),"participants":len(participant_ids),"utterances":len(utterances),"conversation_items":len(items),"review_candidates":sum(i.review_status == "NEEDS_REVIEW" for i in items)}


def _person(store: MeetingMemoryStore, person_id: str) -> dict[str, Any]:
    row = store.row("SELECT * FROM person WHERE person_id=?", (person_id,))
    if row is None:
        raise KeyError(f"unknown person_id: {person_id}")
    return dict(row)


def _accepted_items(store: MeetingMemoryStore, person_id: str) -> list[dict[str, Any]]:
    rows = store.rows("SELECT ci.*,m.started_at,m.title,m.facilitator_person_id FROM conversation_item ci JOIN meeting m ON m.meeting_id=ci.meeting_id WHERE ci.review_status='ACCEPTED' AND (ci.speaker_person_id=? OR ci.owner_person_id=? OR ci.target_person_id=?) ORDER BY m.started_at DESC,ci.item_id DESC",(person_id,person_id,person_id))
    return [_dict_row(r) for r in rows]


def person_card(store: MeetingMemoryStore, person_id: str) -> dict[str, Any]:
    person = _person(store, person_id)
    items = _accepted_items(store, person_id)
    meetings = [dict(r) for r in store.rows("SELECT m.meeting_id,m.title,m.started_at,m.purpose,m.meeting_type FROM meeting m JOIN participant p ON p.meeting_id=m.meeting_id WHERE p.person_id=? ORDER BY m.started_at DESC",(person_id,))]
    facilitator_to_person=[]; person_to_facilitator=[]; agreements=[]; open_items=[]; facts=[]
    for item in items:
        facilitator = item["facilitator_person_id"]
        if facilitator and item["speaker_person_id"] == facilitator and item["target_person_id"] == person_id:
            facilitator_to_person.append(item)
        if facilitator and item["speaker_person_id"] == person_id and item["target_person_id"] == facilitator:
            person_to_facilitator.append(item)
        if item["item_type"] in AGREEMENT_TYPES: agreements.append(item)
        if item["item_type"] in OPEN_TYPES and item["status"] == "OPEN": open_items.append(item)
        if item["item_type"] in FACT_TYPES: facts.append(item)
    review_queue=[_dict_row(r) for r in store.rows("SELECT ci.*,m.started_at,m.title,m.facilitator_person_id FROM conversation_item ci JOIN meeting m ON m.meeting_id=ci.meeting_id WHERE ci.review_status='NEEDS_REVIEW' AND (ci.speaker_person_id=? OR ci.owner_person_id=? OR ci.target_person_id=?) ORDER BY m.started_at DESC",(person_id,person_id,person_id))]
    return {"person":person,"last_meeting":meetings[0] if meetings else None,"meeting_count":len(meetings),"facilitator_to_person":facilitator_to_person,"person_to_facilitator":person_to_facilitator,"agreements_and_commitments":agreements,"open_items":open_items,"facts_and_interests":facts,"timeline":items,"review_queue":review_queue}


def next_meeting_brief(store: MeetingMemoryStore, person_id: str, as_of: str | None = None) -> dict[str, Any]:
    card = person_card(store, person_id)
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()
    open_items=[]; overdue=[]
    for item in card["open_items"]:
        compact={"item_id":item["item_id"],"type":item["item_type"],"summary":item["summary"],"due_date":item["due_date"],"owner_person_id":item["owner_person_id"],"target_person_id":item["target_person_id"],"meeting_id":item["meeting_id"],"evidence_utterance_ids":item["evidence_utterance_ids"]}
        open_items.append(compact)
        if item["due_date"] and date.fromisoformat(item["due_date"]) < as_of_date: overdue.append(compact)
    recent_items=card["timeline"][:20]
    recent_topics=[topic for topic,_ in Counter(x["topic"] for x in recent_items if x["topic"]).most_common(5)]
    latest_facilitator=[{"summary":x["summary"],"meeting_id":x["meeting_id"],"evidence_utterance_ids":x["evidence_utterance_ids"]} for x in card["facilitator_to_person"][:5]]
    latest_requests=[{"summary":x["summary"],"type":x["item_type"],"meeting_id":x["meeting_id"],"evidence_utterance_ids":x["evidence_utterance_ids"]} for x in card["person_to_facilitator"] if x["item_type"] in {"REQUEST","QUESTION","CONCERN","OPEN_ITEM"}][:5]
    check_next=[]; seen=set()
    for item in overdue + open_items + latest_requests:
        if item["summary"] not in seen:
            seen.add(item["summary"]); check_next.append(item)
        if len(check_next) >= 8: break
    return {"person":card["person"],"as_of":as_of_date.isoformat(),"last_meeting":card["last_meeting"],"latest_facilitator_messages":latest_facilitator,"open_commitments_and_requests":open_items,"overdue":overdue,"recent_topics":recent_topics,"latest_person_requests_or_questions":latest_requests,"check_next":check_next,"needs_review_count":len(card["review_queue"]),"retrieval_note":"Brief is generated from accepted structured memory; raw transcripts remain available through evidence references."}


def meeting_record(store: MeetingMemoryStore, meeting_id: str) -> dict[str, Any]:
    meeting = store.row("SELECT * FROM meeting WHERE meeting_id=?", (meeting_id,))
    if meeting is None:
        raise KeyError(f"unknown meeting_id: {meeting_id}")
    participants=[dict(r) for r in store.rows("SELECT p.person_id,p.name,p.organization,p.position FROM participant x JOIN person p ON p.person_id=x.person_id WHERE x.meeting_id=?",(meeting_id,))]
    utterances=[_dict_row(r) for r in store.rows("SELECT * FROM utterance WHERE meeting_id=? ORDER BY start_time,utterance_id",(meeting_id,))]
    items=[_dict_row(r) for r in store.rows("SELECT * FROM conversation_item WHERE meeting_id=? ORDER BY item_id",(meeting_id,))]
    return {"meeting":dict(meeting),"participants":participants,"utterances":utterances,"conversation_items":items}
