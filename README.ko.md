# PromptTailor

> 프롬프트 작성이 어려운 Claude Code 사용자를 위한 도구. 대충 쓴 요청을 **현재 선택된 모델에 가장 어울리는 형태로** 재작성합니다.

[English README](README.md)

## 왜 필요한가

Claude Fable 5 / Opus 5 / Sonnet 5 / Haiku는 잘 반응하는 프롬프트 스타일이 서로 다릅니다 — Fable은 단계 나열 없이 목표·제약을 산문으로, Opus는 검증 지시를 넣으면 과잉 검증, Haiku는 작은 번호 단계를 선호합니다. PromptTailor는 이 차이를 [모델 프로필](prompt_tailor/profiles/) 데이터로 관리하고, 현재 모델을 자동 감지해 맞춤 재작성합니다. 작업 유형(fix/build/research/refactor/docs)별 라우팅도 적용됩니다.

입력 언어는 유지됩니다: 한국어 입력 → 한국어 출력.

## 설치

**Claude Code 플러그인 (권장):**

```
/plugin marketplace add Createyouracccount/PromptTailor
/plugin install prompt-tailor@prompt-tailor
```

**CLI / MCP 서버:**

```bash
pip install prompt-tailor    # prompt-tailor, prompt-tailor-mcp 명령 설치
```

요구사항: Python 3.10+, `claude` CLI 설치·로그인 (별도 API 키 불필요). macOS/Linux 검증됨, Windows 미검증.

## 사용법

```bash
prompt-tailor "대충 쓴 요청" --model fable-5          # 재작성 결과 출력
prompt-tailor "요청" --model haiku-4-5 --json        # JSON 출력
prompt-tailor "요청" --concise                       # 축약 메타프롬프트 (빠름)
```

**Claude Code 안에서** — `/pm 대충 쓴 요청`: 현재 모델에 맞게 재작성 후 변경 요약 한 줄을 보여주고 수행. auto 모드에서 프롬프트에 위험해 보이는 단어가 있으면 분류기가 백엔드를 오탐 차단할 수 있음 — `claude-code/install.sh`가 안내하는 permissions.allow 규칙을 추가하면 해결(백엔드는 텍스트 재작성만 수행).

**훅 자동 모드 (옵트인)** — 모든 프롬프트를 자동 재작성. `bash claude-code/install.sh`가 출력하는 settings 스니펫 참조. `#raw` 태그로 건별 우회, 6토큰 미만·800자 초과는 자동 무개입, 28초 내 미완료 시 원문 그대로 통과(fail-open).

**Cursor 등 MCP 클라이언트** — 내장 stdio MCP 서버가 `refine_prompt(raw, target_model, concise)` 도구 제공:

```jsonc
// ~/.cursor/mcp.json
{ "mcpServers": { "prompt-tailor": { "command": "prompt-tailor-mcp" } } }
```

## 같은 입력, 모델별 변환 차이 (실제 출력)

입력: `로그인 버그 고쳐줘`

| 대상 `fable-5` | 대상 `haiku-4-5` |
|---|---|
| 산문형: 증상 파악을 먼저 지시하고 "원인을 찾아 가장 단순하게 수정, 테스트·수동 검증으로 완료 확인". 단계 나열 없음 | **1단계** 버그 파악(에러? 위치?) → **2단계** 수정([가정] 태그) → **3단계** 정상/오류 자격증명 테스트 → 결과물: 수정 코드 + 커밋 메시지 한 줄 |

전문은 [eval/results.json](eval/results.json).

## 실측 비용 (n=2, 2026-08-15)

| 지불하는 것 | 실측값 |
|---|---|
| 재작성 1회 (haiku) | **API 환산 ≈$0.03** · 출력 ~1.8k 토큰 · 벽시계 18–33초. 입력 ~29.5k 토큰이지만 ~99%는 `claude -p` 자체 시스템 프롬프트(캐시: ~8k 생성 + ~21.6k 읽기) — 우리 메타프롬프트 몫은 수백 토큰 |
| 훅 컨텍스트 주입 | 본 대화에 **+527 입력 토큰**(토큰 델타로 실측), 세션 내내 히스토리에 잔류 |
| 구독 사용자 | 건별 과금 없음 — 사용량 쿼터를 소모 |

원본 데이터: [runs/cost_measurement.json](runs/cost_measurement.json).

## 검증 근거 — 부정적 결과 포함

모든 주장은 원장([LOOP_LOG.md](LOOP_LOG.md))에 기록된 실측 실험(블라인드 쌍대 심판) 기반입니다:

- **프롬프트 품질** (모호한 요청 골든셋 20건): 20/20 원문보다 낫다 (clarity 5.0 · fidelity 4.8 · actionability 5.0) — [EVAL.md](EVAL.md)
- 모델 프로필 구조 차이 5/5, intent 라우팅 4승 1패 1무
- **작업 결과 파일럿 (n=3): 원문 3승 : 재작성 0승.** *이미 명확하고 자기완결적인* 코드 생성 작업을 headless로 실행했을 때 재작성이 오히려 해가 됨 — 범위 부풀림, 조사 지시로 실행 정지, 검증 요구에 가짜 테스트 결과 날조 — [eval/ab_task_outcome_results.json](eval/ab_task_outcome_results.json)

**해석**: 실측된 이득은 **모호하고 불충분한 요청**(골든셋 영역)에 있습니다. 이미 구체적인 요청이면 재작성은 잘해야 오버헤드, 최악엔 해악입니다 — `#raw`(훅)를 쓰거나 `/pm`을 안 쓰면 됩니다. "이미 명확하면 건드리지 않는" 자동 게이트가 로드맵 1순위입니다.

## 보장하지 않는 것

- **실제 작업 성공률 상승은 입증되지 않았습니다.** 품질 승리는 심판 기반이고, 유일한 결과 데이터는 위의 파일럿(원문 승)입니다.
- 재작성기가 가끔 [가정] 표시 없이 세부를 추가하고(fidelity 4.8), intent를 오분류할 수 있습니다.
- 모든 실험은 소표본·단일 심판·이 repo 환경에서 수행됐습니다.

## 개발

```bash
python3 -m unittest discover tests   # 오프라인 테스트 37건 (LLM 호출 없음)
python3 eval/run_eval.py             # 골든셋 평가
```

프로젝트 문서: [PLAN.md](PLAN.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [RESEARCH.md](RESEARCH.md) · 판정 기준 [GATES.md](GATES.md)

## 라이선스

[MIT](LICENSE)
