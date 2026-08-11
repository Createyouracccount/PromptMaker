# LOG — 진행 원장

형식: 날짜 / 한 일 / 확인된 사실 / 결정 / 다음 할 일. 최신이 위.

---

## 2026-08-11 — Phase 1 완료: MVP + 골든셋 평가 통과 ✅

**결과 (상세 EVAL.md)**
- 골든셋 20건 전부 "better" 판정 (DoD ≥16 통과). clarity 4.80 / fidelity 4.10 / actionability 4.85
- 프로필 간 구조적 차이 4/5 입증 (DoD 통과). 실패 1건(g05)은 절차가 내재된 진단 작업에서 프로필이 수렴하는 경계 조건으로 확인

**결정**
- D6: 프로필에는 추상 원칙뿐 아니라 **재작성문의 표면 형식 제약**까지 명시한다 (fable-5 규칙 8 추가로 검증됨)

**다음 할 일 (Phase 2 착수 전 개선)**
- [ ] fidelity 개선: 무단 세부 추가에 [가정] 표시 강제
- [ ] 심판/재작성 호출 자동 재시도 추가
- [ ] opus-5·sonnet-5 프로필 변별력 검증
- [ ] Phase 2: `/pm` 슬래시 커맨드 + UserPromptSubmit 훅, 모델 자동 감지 실측

---

## 2026-08-11 — Phase 1: MVP 구현 (평가 진행 중)

**한 일**
- 패키지 구조: `promptmaker/` (engine.py, cli.py, profiles/), `golden/golden.jsonl`(20개), `eval/run_eval.py`
- 모델 프로필 4종 작성: fable-5 / opus-5 / sonnet-5 / haiku-4-5 + `_common.md`
  - 소스: Anthropic 공식 마이그레이션 가이드(claude-api 스킬 경유)의 모델별 행동 특성. 핵심 차이:
    fable-5 "단계 나열 금지·의도 중심" vs haiku-4-5 "명시적 단계·형식 지정" vs opus-5 "검증 지시 제거·범위 규율"
- 재작성기: `claude -p --model claude-haiku-4-5` + 메타프롬프트(공통규칙+모델프로필), JSON 출력(intent/rewritten/changes)
- 심판: `claude -p --model claude-sonnet-5`, 루브릭(clarity/fidelity/actionability 1~5) + verdict(better/same/worse)
- 스모크 테스트 통과: "로그인 버그 고쳐줘" → 조사 항목·범위·완료 기준이 붙은 프롬프트로 재작성 확인

**확인된 사실**
- `claude -p` 헤드리스 호출로 별도 API 키 없이 재작성 가능 (Claude Code 구독 재사용)

**진행 중**: 골든셋 20개 전체 평가 + 프로필 간 차이 검증 5건 (결과는 eval/results.json, 요약은 EVAL.md에 기록 예정)

---

## 2026-08-11 — Phase 0: 조사·기획 완료

**한 일**: 유사 프로젝트 조사(웹), 훅 스펙 확인(공식 문서), 아키텍처·로드맵 문서화.

**확인된 사실**
1. 동일 컨셉 오픈소스 3종 존재 (severity1, GaZmagik, scooter-lacroix) + Anthropic 공식 Prompt Improver. 상세 RESEARCH.md.
2. 전부 "일반적으로 좋은 프롬프트"로 개선할 뿐, **모델별 맞춤 재작성은 아무도 안 함**.
3. UserPromptSubmit 훅은 **프롬프트 교체 불가** — additionalContext 주입 또는 block만 가능.
4. GaZmagik의 실측 한계: 재작성당 수 초~수십 초 지연, 단문(<10토큰) 스킵 필요.

**결정**
- D1: 재작성은 LLM(메타프롬프트), 모델별 차이는 데이터 파일(profiles/*.md)로 관리
- D2: MVP는 독립 CLI부터 (훅/플러그인/MCP는 이후 어댑터)
- D3: Claude Code 통합은 옵트인 슬래시 커맨드 기본 + 훅 자동 모드 선택
- D4: 재작성 결과에 변경 요약 항상 표시 (교육 효과)
- D5: Python + uv, LLM 호출은 1차로 `claude -p`

**다음 할 일 (Phase 1)**
- [ ] profiles/ 4종 작성 (fable-5, opus-5, sonnet-5, haiku-4-5) — 공식 프롬프팅 가이드부터 수집
- [ ] 골든셋 15~20개 구축
- [ ] 코어 파이프라인 구현 → 골든셋 평가 → 프로필 간 차이 검증 (DoD: 20개 중 16개 개선 판정)
