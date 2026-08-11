# RESEARCH — 기존 프로젝트 조사 및 벤치마킹 (2026-08-11)

## 결론 요약

- **완전히 같은 것을 하는 프로젝트는 이미 여러 개 존재한다.** Claude Code의 UserPromptSubmit 훅으로 프롬프트를 개선하는 오픈소스가 최소 3개, Anthropic 공식 Prompt Improver(Console)도 있다.
- **그러나 "선택된 모델에 맞춘 재작성(model-aware rewriting)"을 하는 곳은 없다.** 기존 도구는 전부 "일반적으로 좋은 프롬프트"로 개선할 뿐, Fable 5 / Opus 5 / Sonnet / Haiku의 스타일 차이를 반영하지 않는다. → **이것이 우리의 차별화 축.**
- **크로스 클라이언트(클라이언트 무관) 지원을 명시적으로 설계한 곳도 없다.** 전부 Claude Code 플러그인/훅 전용. Cursor 네이티브·기타 클라이언트까지 커버하려면 MCP 서버 형태가 필요하다. → 두 번째 차별화 축.

## 1. 공식 도구: Anthropic Prompt Improver

- Anthropic Console 내장 기능. 기존 프롬프트를 chain-of-thought 등 프롬프트 엔지니어링 기법으로 자동 개선.
- 성과 수치: 다중 라벨 분류 정확도 +30%, 요약 단어 수 준수 100% 달성 주장.
- 예시 관리 + 평가(Evaluator) 도구가 붙어 있음 → **"개선 → 평가" 루프가 한 세트라는 점을 벤치마킹할 것.**
- 한계: Console(웹) 안에서만 동작. Claude Code 워크플로우와 분리되어 있고, API 개발자용 시스템 프롬프트 개선에 초점.
- 출처: https://claude.com/blog/prompt-improver , https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-tools

## 2. 오픈소스: Claude Code 프롬프트 개선 훅 3종

### 2-1. severity1/claude-code-prompt-improver ★ 구조 벤치마킹 1순위
- https://github.com/severity1/claude-code-prompt-improver
- 아키텍처: **선언적 JSON 규칙("nudges") + 이를 평가하는 엔진(engine.py)**. Python 수정 없이 JSON만 추가해 기능 확장.
- 훅 3종 사용: UserPromptSubmit / PreToolUse / SubagentStart.
- 항상 실행 2개(improve: 명확성 검증 ~189토큰, plan-mode: 복잡도 판단) + 조건부 7개.
- 배포: Claude Code 플러그인 마켓플레이스.
- 배울 점: **규칙을 데이터(JSON)로 분리한 구조** — 우리의 "모델 프로필"도 같은 방식(데이터 파일)으로 가면 됨. 토큰 오버헤드를 버전마다 측정·절감(275→189, -31%)하는 운영 방식도 참고.

### 2-2. GaZmagik/claude-prompt-improver ★ UX 벤치마킹 1순위
- https://github.com/GaZmagik/claude-prompt-improver
- Bun/TypeScript 플러그인. 분류→개선→컨텍스트 주입 계층 구조.
- **옵트인 UX**: 기본은 `#improve` 태그를 붙인 프롬프트만 개선, 설정으로 전체 자동화 가능. → 자동 개입에 대한 거부감 해소책으로 참고.
- "Prose-first structuring": 목표/근거 우선, 범위, 번호 질문, 명확한 결과물 순으로 재구성.
- `improverModel` 설정으로 개선 작업에 쓸 모델(Haiku/Sonnet/Opus) 선택 — **주의: 이것은 "개선기를 돌릴 모델" 선택이지, "대상 모델에 맞춘 재작성"이 아님.**
- 장르별 조건부 템플릿(수정/조사/연구/구축/일반) + 개인 예시 라이브러리.
- 한계(우리도 겪을 문제): 개선당 수 초~수십 초 지연, 10토큰 미만 단문은 스킵, 타임아웃 관리 필요.

### 2-3. scooter-lacroix/claude-code-prompt-enhancer
- https://github.com/scooter-lacroix/claude-code-prompt-enhancer
- 컨텍스트·예시·구조화 가이드를 자동 추가하는 훅 시스템. 위 둘보다 단순.

### 2-4. 참고: disler/claude-code-hooks-mastery
- https://github.com/disler/claude-code-hooks-mastery — 훅 라이프사이클 전반의 레퍼런스 구현. 훅 구현 시 참고서로 사용.

## 3. 학술/범용 프롬프트 최적화 계열 (직접 경쟁 아님, 기법 참고)

- **DSPy**: 프롬프트를 "가중치"로 보고 데이터 기반 자동 최적화. 모델 무관 시그니처로 모델 교체 시 프롬프트 재작성 불필요를 지향 — 우리와 반대 방향(우리는 모델별 차이를 *활용*). 다만 "평가셋 기반 자동 튜닝" 개념은 Phase 4에서 모델 프로필을 데이터로 검증할 때 차용 가능.
- **PromptPerfect**: 상용. 대상 LLM을 지정하면 그에 맞게 프롬프트를 다듬어줌 — **모델별 맞춤이라는 점에서 우리와 가장 유사한 발상.** 단, 범용 웹 서비스이고 코딩 에이전트(Claude Code) 워크플로우 통합이 없음.
- Promptomatix, APO 서베이 등 자동 프롬프트 최적화 논문군: 필요 시 Phase 4에서 참조.

## 4. 기술적 제약 (공식 문서 확인, 2026-08-11)

Claude Code `UserPromptSubmit` 훅 스펙 (출처: https://code.claude.com/docs/en/hooks):

| 가능 여부 | 항목 |
|---|---|
| ❌ | **프롬프트 텍스트 자체를 수정/교체** — 공식적으로 불가 |
| ✅ | `hookSpecificOutput.additionalContext`로 컨텍스트 주입 (여러 훅 누적 가능) |
| ✅ | `decision: "block"` + `reason`으로 프롬프트 차단 (reason이 Claude에게 전달됨) |
| ✅ | `systemMessage`로 사용자에게 경고 표시 |
| - | 훅 타임아웃 기본 30초 |

**함의**: 훅만으로는 "재작성한 프롬프트로 교체"가 불가능. 실현 경로는 3가지:
1. **additionalContext 방식** — 원래 프롬프트는 그대로 두고 "이 요청을 다음과 같이 해석·수행하라"는 재해석 지시를 주입. (자동 모드에 적합, 기존 3개 프로젝트가 실질적으로 쓰는 방식)
2. **슬래시 커맨드/스킬 방식** — `/pm <원문>` 형태로 명시 호출하면 스킬 내부에서 재작성 후 수행. (프롬프트를 완전히 통제 가능, 옵트인)
3. **독립 CLI/MCP 방식** — Claude Code 밖에서 재작성된 텍스트를 돌려주고 사용자가 붙여넣거나, MCP 도구로 노출. (Cursor 등 타 클라이언트 커버)

## 5. 벤치마킹 채택 사항 정리

| 항목 | 출처 | 채택 내용 |
|---|---|---|
| 규칙의 데이터화 | severity1 | 모델 프로필을 코드가 아닌 데이터 파일(YAML/JSON/MD)로 관리 |
| 옵트인 → 자동 전환 UX | GaZmagik | 기본 옵트인(명시 호출), 신뢰 쌓이면 자동 모드 제공 |
| 장르 분류 → 템플릿 | GaZmagik | 의도 분류(수정/구축/조사/디버그) 후 템플릿 적용 |
| 개선→평가 한 세트 | Anthropic 공식 | 골든셋 + before/after 평가를 처음부터 내장 |
| 토큰 오버헤드 계측 | severity1 | 주입 토큰 수를 버전마다 측정·기록 |

## 미확인/추후 검증 필요

- [ ] 훅 입력에 **현재 선택된 모델 ID**가 포함되는지 (문서상 session_id, cwd 등만 확인됨. 미포함이면 `claude config get model`·settings.json·환경변수로 감지해야 함) — Phase 2 착수 시 실측
- [ ] Cursor 네이티브(Claude Code 미사용) 사용자의 정확한 통합 지점 — MCP 서버로 가정 중, Phase 3에서 검증
- [ ] Claude Code 플러그인 마켓플레이스 등록 절차
