from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

ITEM_TYPES = {"FACT","OPINION","QUESTION","ANSWER","REQUEST","INSTRUCTION","PROMISE","PROPOSAL","CONCERN","DECISION","OPEN_ITEM","INTEREST","POSITION","PERSONAL_FACT"}
REVIEW_STATES = {"ACCEPTED", "NEEDS_REVIEW", "REJECTED"}
ITEM_STATES = {"OPEN", "DONE", "SUPERSEDED", "CANCELLED"}


def _require(value: Any, name: str) -> Any:
    if value in (None, ""):
        raise ValueError(f"{name} is required")
    return value


@dataclass(frozen=True)
class Person:
    person_id: str
    name: str
    organization: str | None = None
    position: str | None = None
    role: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Person":
        return cls(str(_require(data.get("person_id"), "person_id")), str(_require(data.get("name"), "name")), data.get("organization"), data.get("position"), data.get("role"))


@dataclass(frozen=True)
class Meeting:
    meeting_id: str
    title: str
    started_at: str
    purpose: str | None = None
    meeting_type: str | None = None
    ended_at: str | None = None
    location: str | None = None
    facilitator_person_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Meeting":
        return cls(str(_require(data.get("meeting_id"), "meeting_id")), str(_require(data.get("title"), "title")), str(_require(data.get("started_at"), "started_at")), data.get("purpose"), data.get("meeting_type"), data.get("ended_at"), data.get("location"), data.get("facilitator_person_id"))


@dataclass(frozen=True)
class Utterance:
    utterance_id: str
    meeting_id: str
    speaker_person_id: str | None
    start_time: str | None
    end_time: str | None
    text: str
    addressee_person_ids: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, meeting_id: str, data: dict[str, Any]) -> "Utterance":
        return cls(str(_require(data.get("utterance_id"), "utterance_id")), meeting_id, data.get("speaker_person_id"), data.get("start_time"), data.get("end_time"), str(_require(data.get("text"), "text")), tuple(str(x) for x in data.get("addressee_person_ids", [])))


@dataclass(frozen=True)
class ConversationItem:
    item_id: str
    meeting_id: str
    item_type: str
    summary: str
    status: str = "OPEN"
    speaker_person_id: str | None = None
    owner_person_id: str | None = None
    target_person_id: str | None = None
    due_date: str | None = None
    topic: str | None = None
    confidence: float = 1.0
    review_status: str = "ACCEPTED"
    evidence_utterance_ids: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, meeting_id: str, data: dict[str, Any]) -> "ConversationItem":
        item_type = str(_require(data.get("item_type"), "item_type")).upper()
        status = str(data.get("status", "OPEN")).upper()
        review_status = str(data.get("review_status", "ACCEPTED")).upper()
        confidence = float(data.get("confidence", 1.0))
        if item_type not in ITEM_TYPES: raise ValueError(f"unsupported item_type: {item_type}")
        if status not in ITEM_STATES: raise ValueError(f"unsupported status: {status}")
        if review_status not in REVIEW_STATES: raise ValueError(f"unsupported review_status: {review_status}")
        if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        due_date = data.get("due_date")
        if due_date: date.fromisoformat(str(due_date))
        return cls(str(_require(data.get("item_id"), "item_id")), meeting_id, item_type, str(_require(data.get("summary"), "summary")), status, data.get("speaker_person_id"), data.get("owner_person_id"), data.get("target_person_id"), str(due_date) if due_date else None, data.get("topic"), confidence, review_status, tuple(str(x) for x in data.get("evidence_utterance_ids", [])))
