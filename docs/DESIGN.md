# Design notes

## Two linked views, one source of truth

A meeting produces two views:

1. **Meeting Record** — the meeting, participants, utterances, structured items, and evidence links.
2. **Person Memory** — a derived person-centric view over the same accepted structured items.

The public core does not duplicate the transcript into every person card.

## Store much, read little

Raw utterances and structured items can be retained in SQLite. A next-meeting brief retrieves only the small set needed for the next conversation: last meeting, recent facilitator messages, open commitments/requests, overdue items, recent topics, and items to verify next.

## Evidence before memory

Every structured conversation item can point to one or more `utterance_id` values. `NEEDS_REVIEW` items remain visible in a review queue but do not enter accepted long-term person memory.

## Provider-neutral boundary

The v0.1 public core begins **after** speech-to-text / diarization / AI extraction. Any model can be connected by producing the JSON contract used by `ingest`. Microphone capture, STT, speaker identification, embeddings, and LLM extraction are adapters rather than hard dependencies.

## Public scope

All examples are synthetic. This repository contains no private meeting audio, transcripts, people, company data, or internal model endpoints.
