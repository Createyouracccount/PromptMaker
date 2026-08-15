# PromptMaker

> 프롬프트 작성이 어려운 Claude Code 사용자를 위한 도구. 대충 쓴 요청을 **현재 선택된 모델에 가장 어울리는 형태로** 재작성합니다.

[English README](README.md)

## 왜 필요한가

Claude Fable 5 / Opus 5 / Sonnet 5 / Haiku는 잘 반응하는 프롬프트 스타일이 서로 다릅니다 — Fable은 단계 나열 없이 목표·제약을 산문으로, Opus는 검증 지시를 넣으면 과잉 검증, Haiku는 작은 번호 단계를 선호합니다. PromptMaker는 이 차이를 [모델 프로필](promptmaker/profiles/) 데이터로 관리하고, 현재 모델을 자동 감지해 맞춤 재작성합니다. 작업 유형(fix/build/research/refactor/docs)별 라우팅도 적용됩니다.

입력 언어는 유지됩니다: 한국어 입력 → 한국어 출력.

## 설치

**Claude Code 플러그인 (권장):**

```
/plugin marketplace add Createyouracccount/PromptMaker
/plugin install promptmaker@promptmaker
```

**CLI / MCP 서버:**

```bash
git clone https://github.com/Createyouracccount/PromptMaker.git
cd PromptMaker
pip install .            # promptmaker, promptmaker-mcp 명령 설치
```

요구사항: Python 3.10+, `claude` CLI 설치·로그인 (별도 API 키 불필요). macOS/Linux 검증됨, Windows 미검증.

## 사용법

```bash
promptmaker "대충 쓴 요청" --model fable-5          # 재작성 결과 출력
promptmaker "요청" --model haiku-4-5 --json        # JSON 출력
promptmaker "요청" --concise                       # 축약 메타프롬프트 (빠름)
```

**Claude Code 안에서** — `/pm 대충 쓴 요청`: 현재 모델에 맞게 재작성 후 변경 요약 한 줄을 보여주고 수행. auto 모드에서 프롬프트에 위험해 보이는 단어가 있으면 분류기가 백엔드를 오탐 차단할 수 있음 — `claude-code/install.sh`가 안내하는 permissions.allow 규칙을 추가하면 해결(백엔드는 텍스트 재작성만 수행).

**훅 자동 모드 (옵트인)** — 모든 프롬프트를 자동 재작성. `bash claude-code/install.sh`가 출력하는 settings 스니펫 참조. `#raw` 태그로 건별 우회, 6토큰 미만·800자 초과는 자동 무개입, 28초 내 미완료 시 원문 그대로 통과(fail-open).

**Cursor 등 MCP 클라이언트** — 내장 stdio MCP 서버가 `refine_prompt(raw, target_model, concise)` 도구 제공:

```jsonc
// ~/.cursor/mcp.json
{ "mcpServers": { "promptmaker": { "command": "promptmaker-mcp" } } }
```

## 검증 근거

모든 설계 결정은 실측 실험(블라인드 쌍대 LLM 심판)으로 뒷받침되며 [LOOP_LOG.md](LOOP_LOG.md) 원장에 기록되어 있습니다:

- 골든셋 20건: **20/20 원문보다 낫다 판정** (clarity 5.0 · fidelity 4.8 · actionability 5.0) — [EVAL.md](EVAL.md)
- 모델 프로필 간 구조적 차이: 5/5
- intent 라우팅이 프로필 단독 대비 쌍대 4승 1패 1무
- 재작성 지연 ~15–30초 (`claude -p` 경로 — API 키가 필요 없는 대신의 비용)

정직한 한계는 [EVAL.md](EVAL.md) 참조: 표본 작음, 단일 LLM 심판, "더 나은 프롬프트" ≠ 실제 태스크 성공률 상승 입증.

## 개발

```bash
python3 -m unittest discover tests   # 오프라인 테스트 37건 (LLM 호출 없음)
python3 eval/run_eval.py             # 골든셋 평가
```

프로젝트 문서: [PLAN.md](PLAN.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [RESEARCH.md](RESEARCH.md) · 판정 기준 [GATES.md](GATES.md)

## 라이선스

[MIT](LICENSE)
