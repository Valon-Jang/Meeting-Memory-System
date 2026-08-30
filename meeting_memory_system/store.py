from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import ConversationItem, Meeting, Person, Utterance

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS person (person_id TEXT PRIMARY KEY,name TEXT NOT NULL,organization TEXT,position TEXT,role TEXT);
CREATE TABLE IF NOT EXISTS meeting (meeting_id TEXT PRIMARY KEY,title TEXT NOT NULL,purpose TEXT,meeting_type TEXT,started_at TEXT NOT NULL,ended_at TEXT,location TEXT,facilitator_person_id TEXT);
CREATE TABLE IF NOT EXISTS participant (meeting_id TEXT NOT NULL,person_id TEXT NOT NULL,role TEXT,PRIMARY KEY (meeting_id, person_id),FOREIGN KEY (meeting_id) REFERENCES meeting(meeting_id) ON DELETE CASCADE,FOREIGN KEY (person_id) REFERENCES person(person_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS utterance (utterance_id TEXT PRIMARY KEY,meeting_id TEXT NOT NULL,speaker_person_id TEXT,start_time TEXT,end_time TEXT,text TEXT NOT NULL,addressee_person_ids_json TEXT NOT NULL,FOREIGN KEY (meeting_id) REFERENCES meeting(meeting_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS conversation_item (item_id TEXT PRIMARY KEY,meeting_id TEXT NOT NULL,item_type TEXT NOT NULL,summary TEXT NOT NULL,status TEXT NOT NULL,speaker_person_id TEXT,owner_person_id TEXT,target_person_id TEXT,due_date TEXT,topic TEXT,confidence REAL NOT NULL,review_status TEXT NOT NULL,evidence_utterance_ids_json TEXT NOT NULL,FOREIGN KEY (meeting_id) REFERENCES meeting(meeting_id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_item_person_owner ON conversation_item(owner_person_id);
CREATE INDEX IF NOT EXISTS idx_item_person_target ON conversation_item(target_person_id);
CREATE INDEX IF NOT EXISTS idx_item_person_speaker ON conversation_item(speaker_person_id);
CREATE INDEX IF NOT EXISTS idx_item_status ON conversation_item(status, review_status);
CREATE INDEX IF NOT EXISTS idx_meeting_started ON meeting(started_at);
"""


class MeetingMemoryStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def ingest(self, people: Iterable[Person], meeting: Meeting, participant_ids: Iterable[str], utterances: Iterable[Utterance], items: Iterable[ConversationItem]) -> None:
        with self.conn:
            for p in people:
                self.conn.execute("INSERT INTO person(person_id,name,organization,position,role) VALUES(?,?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET name=excluded.name,organization=COALESCE(excluded.organization,person.organization),position=COALESCE(excluded.position,person.position),role=COALESCE(excluded.role,person.role)",(p.person_id,p.name,p.organization,p.position,p.role))
            self.conn.execute("INSERT INTO meeting(meeting_id,title,purpose,meeting_type,started_at,ended_at,location,facilitator_person_id) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(meeting_id) DO UPDATE SET title=excluded.title,purpose=excluded.purpose,meeting_type=excluded.meeting_type,started_at=excluded.started_at,ended_at=excluded.ended_at,location=excluded.location,facilitator_person_id=excluded.facilitator_person_id",(meeting.meeting_id,meeting.title,meeting.purpose,meeting.meeting_type,meeting.started_at,meeting.ended_at,meeting.location,meeting.facilitator_person_id))
            self.conn.execute("DELETE FROM participant WHERE meeting_id=?", (meeting.meeting_id,))
            for person_id in participant_ids:
                self.conn.execute("INSERT INTO participant(meeting_id,person_id,role) VALUES(?,?,NULL)",(meeting.meeting_id,person_id))
            for u in utterances:
                self.conn.execute("INSERT INTO utterance(utterance_id,meeting_id,speaker_person_id,start_time,end_time,text,addressee_person_ids_json) VALUES(?,?,?,?,?,?,?) ON CONFLICT(utterance_id) DO UPDATE SET meeting_id=excluded.meeting_id,speaker_person_id=excluded.speaker_person_id,start_time=excluded.start_time,end_time=excluded.end_time,text=excluded.text,addressee_person_ids_json=excluded.addressee_person_ids_json",(u.utterance_id,u.meeting_id,u.speaker_person_id,u.start_time,u.end_time,u.text,json.dumps(u.addressee_person_ids)))
            for i in items:
                self.conn.execute("INSERT INTO conversation_item(item_id,meeting_id,item_type,summary,status,speaker_person_id,owner_person_id,target_person_id,due_date,topic,confidence,review_status,evidence_utterance_ids_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET meeting_id=excluded.meeting_id,item_type=excluded.item_type,summary=excluded.summary,status=excluded.status,speaker_person_id=excluded.speaker_person_id,owner_person_id=excluded.owner_person_id,target_person_id=excluded.target_person_id,due_date=excluded.due_date,topic=excluded.topic,confidence=excluded.confidence,review_status=excluded.review_status,evidence_utterance_ids_json=excluded.evidence_utterance_ids_json",(i.item_id,i.meeting_id,i.item_type,i.summary,i.status,i.speaker_person_id,i.owner_person_id,i.target_person_id,i.due_date,i.topic,i.confidence,i.review_status,json.dumps(i.evidence_utterance_ids)))

    def rows(self, query: str, params: tuple = ()):
        return list(self.conn.execute(query, params))

    def row(self, query: str, params: tuple = ()):
        return self.conn.execute(query, params).fetchone()
