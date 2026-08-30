# Meeting Memory System

한 번의 회의록을 잘 만드는 도구가 아니라, **사람별 대화 기억을 다음 만남까지 이어가는 시스템**의 공개 코어입니다.

> 다음에 이 사람을 만났을 때, 지난 대화에서 무엇을 기억하고 있어야 하는가?

## 왜 만들었나

회의록은 보통 **그 회의에서 무슨 일이 있었는지**는 잘 남깁니다. 그런데 같은 사람을 다음에 다시 만났을 때 **내가 무엇을 기억해야 하는지**는 잘 남기지 못합니다.

대화를 여러 번 이어가다 보면 중요한 내용은 회의별 기록 사이에 흩어집니다. 내가 그 사람에게 무슨 말을 했는지, 그 사람이 나에게 무엇을 요청했는지, 내가 무엇을 약속했는지, 상대가 무엇을 약속했는지, 무엇에 합의했고 무엇이 아직 미해결인지가 각각 다른 회의록 속에 남게 됩니다.

그래서 다음 만남 전에 이런 질문에 바로 답할 수 있는 시스템을 만들고 싶었습니다.

- 지난번에 내가 이 사람에게 무엇을 말했는가?
- 이 사람이 나에게 무엇을 말하거나 요청했는가?
- 서로 무엇을 약속했는가?
- 아직 해결되지 않았거나 기한이 지난 것은 무엇인가?
- 이번에 다시 만났을 때 무엇을 기억하고 확인해야 하는가?

이 문제에서 **Meeting Memory System**이 시작됐습니다. 회의 원문과 Evidence는 그대로 보존하되, 그 위에 사람 중심의 지속적인 기억 계층을 만들어 새로운 대화가 이전 대화의 Context에서 이어지게 하는 것이 목표입니다.

## v0.1 핵심

- 사람 / 회의 / 참석자 / 발언 / 구조화 대화 항목을 SQLite에 저장
- 각 기억 항목에서 `utterance_id`로 원문 Evidence 추적
- **Meeting Record**와 **Person Memory**를 같은 원본 데이터에서 생성
- 사람 카드 우선순위: 진행자가 그 사람에게 한 말 → 그 사람이 진행자에게 한 말 → 합의·약속 → 요청·지시 → 미해결 질문·후속조치 → 확인된 사실·관심사
- 다음 만남 전 `Next Meeting Brief` 생성: 마지막 만남, 최근 진행자 메시지, 미완료 요청·약속, 기한 초과, 최근 주제, 이번에 확인할 것
- `ACCEPTED`와 `NEEDS_REVIEW`를 분리해 불확실한 AI 추론이 장기 기억으로 자동 승격되지 않도록 함
- 특정 LLM/STT/회의 플랫폼에 종속되지 않는 JSON 계약

## 범위

이 공개 v0.1은 **음성 전사와 AI 분석이 끝난 이후의 기억 계층**을 구현합니다. 현재 마이크 녹음, 실시간 STT, 화자 분리, 음성 기반 인물 식별, LLM 자동 추출까지 구현했다고 주장하지 않습니다. 이 기능들은 Adapter로 연결할 수 있습니다.

## 실행

```bash
python -m meeting_memory_system --db demo.db ingest examples/synthetic_meeting.json --pretty
python -m meeting_memory_system --db demo.db person P-MINA --pretty
python -m meeting_memory_system --db demo.db brief P-MINA --as-of 2026-09-03 --pretty
```

설치형 CLI:

```bash
python -m pip install -e .
meeting-memory --db demo.db ingest examples/synthetic_meeting.json --pretty
meeting-memory --db demo.db brief P-MINA --as-of 2026-09-03 --pretty
```

테스트:

```bash
python -m unittest discover -s tests -v
```

## 핵심 구조

```text
Meeting -> Utterance -> Conversation Item -> Evidence
                            |              |
                            +-> 회의 기록  |
                            +-> 사람 기억 <-+
                                   |
                                   +-> 다음 만남 브리핑
```

사람 카드는 원문을 계속 복사하는 두 번째 회의록이 아닙니다. 필요한 구조화 기억만 작게 유지하고, 상세 내용이 필요할 때 Evidence를 통해 원문으로 돌아갑니다.

## 기억 후보 정책

- `ACCEPTED`: 장기 Person Memory와 브리핑에 사용
- `NEEDS_REVIEW`: 확인 후보로만 유지
- `REJECTED`: 장기 기억에서 제외

즉 **많이 저장하되, 다음 판단에는 검증된 작은 기억만 읽는 구조**입니다.

## 공개 데이터 원칙

예제는 전부 합성 데이터입니다. 실제 회사 회의, 사람 이름, 음성, 전사문, 조직 정보, 사내 AI Endpoint는 포함하지 않습니다.

## License

MIT
