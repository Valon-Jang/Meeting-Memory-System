# Meeting Memory System

A persistent meeting-memory core that keeps track of **people, conversations, requests, commitments, decisions, evidence, and follow-ups across meetings**.

Most meeting tools optimize for the document produced at the end of one meeting. This project explores a different question:

> **What should the system remember about each person so the next conversation can continue from where the last one ended?**

[한국어 README](README_KO.md)

## Why I built this

Meeting notes are good at telling me **what happened in a meeting**. They are much worse at telling me **what I should remember the next time I meet the same person**.

Across repeated conversations, the details that matter tend to scatter: what I told someone, what they asked me to do, what I promised, what they promised, what we agreed on, and what was left unresolved. Even when every meeting has a summary, that context is still easy to lose because it is organized by meeting rather than by relationship and continuity.

I wanted a system that could answer a more practical set of questions before the next conversation:

- What did I tell this person last time?
- What did they tell or ask me?
- What did either of us promise?
- What is still unresolved or overdue?
- What should I remember or verify when we meet again?

That became the idea behind **Meeting Memory System**: keep the original meeting evidence, but build a persistent person-centered memory layer on top of it so each new conversation can start with the context of the previous ones.

## Why this exists

A meeting summary is useful once. A memory system should still be useful months later.

```text
Meeting -> utterances -> structured conversation items -> evidence
                                  |                    |
                                  +--> Meeting Record  |
                                  +--> Person Memory <-+
                                             |
                                             +--> Next Meeting Brief
```

The system keeps the **Meeting Record** and **Person Memory** as two views over the same evidence instead of copying summaries into disconnected notes.

## What v0.1 does

- Stores people, meetings, participants, utterances, and structured conversation items in SQLite.
- Keeps evidence links from memory items back to exact utterance IDs.
- Builds a person card that prioritizes:
  1. what the facilitator told that person,
  2. what that person told the facilitator,
  3. agreements and commitments,
  4. requests / promises / instructions,
  5. unresolved questions and follow-ups,
  6. accepted facts and interests.
- Generates a compact **Next Meeting Brief** containing the last meeting, open items, overdue commitments, recent topics, and what should be checked next.
- Separates `ACCEPTED` long-term memory from `NEEDS_REVIEW` candidates.
- Makes ingestion idempotent with stable IDs.
- Uses a provider-neutral JSON interface. No specific LLM, STT engine, calendar, or meeting platform is required.

## What v0.1 does not do

This public core begins after transcription/analysis. It does **not** claim to implement microphone capture, real-time STT, diarization, voice identification, or automatic LLM extraction yet. Those belong in adapters around the memory core.

## Quick start

Python 3.10+.

```bash
python -m meeting_memory_system --db demo.db ingest examples/synthetic_meeting.json --pretty
python -m meeting_memory_system --db demo.db person P-MINA --pretty
python -m meeting_memory_system --db demo.db brief P-MINA --as-of 2026-09-03 --pretty
```

Install the CLI:

```bash
python -m pip install -e .
meeting-memory --db demo.db ingest examples/synthetic_meeting.json --pretty
meeting-memory --db demo.db brief P-MINA --as-of 2026-09-03 --pretty
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Input contract

A meeting JSON contains:

```json
{
  "people": [],
  "meeting": {},
  "participant_ids": [],
  "utterances": [],
  "conversation_items": []
}
```

A conversation item is structured and evidence-linked:

```json
{
  "item_id": "I-002",
  "item_type": "PROMISE",
  "summary": "Alex promised Mina to confirm the revised validation window by Tuesday.",
  "status": "OPEN",
  "speaker_person_id": "P-HOST",
  "owner_person_id": "P-HOST",
  "target_person_id": "P-MINA",
  "due_date": "2026-09-01",
  "topic": "validation schedule",
  "confidence": 0.99,
  "review_status": "ACCEPTED",
  "evidence_utterance_ids": ["U-002"]
}
```

Supported types include `FACT`, `QUESTION`, `REQUEST`, `INSTRUCTION`, `PROMISE`, `DECISION`, `OPEN_ITEM`, `INTEREST`, `POSITION`, and others defined in the package.

## Memory safety rule

A low-confidence model guess should not silently become permanent memory.

- `ACCEPTED` — included in person memory and briefs.
- `NEEDS_REVIEW` — visible as a candidate but excluded from accepted memory.
- `REJECTED` — excluded from long-term memory.

## Design principles

**Person memory is not a second transcript.** It is a small, structured retrieval layer over source evidence.

**Evidence stays attached.** Important memory should be inspectable against the original utterance.

**Store much, read little.** Long-term storage can be large while the next-meeting brief remains small.

**Models are adapters.** The memory engine should survive a change of LLM, STT system, or meeting platform.

**Uncertainty is explicit.** Review candidates do not silently become facts.

See [docs/DESIGN.md](docs/DESIGN.md).

## Roadmap

- Longitudinal multi-meeting tests
- Follow-up resolution commands
- Full-text search
- Current-value and position-change tracking
- Model extraction adapter contract
- STT / diarization adapters
- Optional scheduler integration after explicit user approval
- Lightweight UI

## Privacy

This repository contains only synthetic examples. Do not commit private recordings, transcripts, real people, private organizational data, or internal model endpoints.

## License

MIT
