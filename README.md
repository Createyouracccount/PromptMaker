# PromptMaker

> 프롬프트 작성에 어려움을 겪는 사람들을 돕는 도구.
> 사용자가 하고 싶은 말을 대충 적으면, **현재 선택된 모델에 가장 어울리는 형태로** 프롬프트를 다듬어주는 프로그램.

## 한 줄 정의

**입력**: 사용자의 날것 그대로의 요청(raw prompt) + 대상 모델(예: Fable 5, Opus 5) + 프로젝트 컨텍스트
**출력**: 해당 모델의 프롬프팅 특성에 맞게 재작성된 프롬프트

## 핵심 원칙

1. **모델별 맞춤(model-aware)** — Fable 5, Opus 5, Sonnet 5, Haiku는 각각 잘 반응하는 프롬프트 스타일이 다르다. 모델 프로필을 데이터로 관리하고, 선택된 모델에 맞춰 재작성한다. ← 기존 도구들이 안 하는 우리의 차별점.
2. **클라이언트 무관(client-agnostic)** — VSCode 확장, CMD(CLI), Cursor 등 어디서 쓰든 동일하게 동작. 코어 엔진 하나 + 배포 어댑터 여러 개 구조로 해결.
3. **문서 주도 진행** — 확인된 사실은 이 폴더에 즉시 기록하고, 다음 계획은 기록 위에서 세운다.

## 문서 구조

| 파일 | 내용 |
|---|---|
| [RESEARCH.md](RESEARCH.md) | 기존 유사 프로젝트 조사·벤치마킹 결과 (2026-08-11) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 설계, 기술적 제약, 설계 결정 |
| [PLAN.md](PLAN.md) | 단계별 로드맵과 각 단계의 완료 기준 |
| [LOG.md](LOG.md) | 진행 원장 — 날짜별 확인 사실·결정·다음 할 일 |

## 설치 (Quick Start)

```bash
git clone https://github.com/Createyouracccount/PromptMaker.git
cd PromptMaker
pip install .                    # promptmaker CLI 설치
bash claude-code/install.sh      # /pm 슬래시 커맨드 설치 (Claude Code용, 선택)
```

## 사용법

```bash
promptmaker "대충 쓴 요청" --model fable-5          # 재작성 결과 출력
promptmaker "요청" --model haiku-4-5 --json        # JSON 출력
promptmaker "요청" --concise                       # 축약 메타프롬프트 (빠름, 훅과 동일 경로)
python3 eval/run_eval.py                           # 골든셋 평가 (repo 안에서)
python3 -m unittest discover tests                 # 오프라인 테스트 (LLM 호출 없음)
```

Claude Code 안에서: `/pm 대충 쓴 요청` → 현재 모델에 맞게 재작성 후 수행.
훅 자동 모드: install.sh가 출력하는 settings 스니펫 참조. `#raw` 태그로 우회, 10토큰 미만·800자 초과는 자동 무개입.

요구사항: Python 3.10+, `claude` CLI 설치·로그인 (별도 API 키 불필요). macOS/Linux 검증됨, Windows 미검증.

## 현재 상태

- **Phase 0 (조사·기획): 완료** — 2026-08-11
- **Phase 1 (MVP): 완료** — 2026-08-11. 골든셋 20/20 "better", 프로필 간 차이 5/5 입증 ([EVAL.md](EVAL.md))
- **Phase 2 (Claude Code 통합): 완료 — 게이트 5/5 PASS** — 2026-08-11. /pm 커맨드 + 훅 자동 모드(축약 메타로 재작성 ~15-19s) 모두 심판 검증 통과 ([LOOP_LOG.md](LOOP_LOG.md) R7)
- 개선 루프 인프라: [GATES.md](GATES.md)(동결 기준) + [LOOP_LOG.md](LOOP_LOG.md)(원장) + [PROMPT.md](PROMPT.md)(세션 재개 블록)
- 다음: Phase 3 (MCP 서버로 Cursor 지원) — 게이트 초안 사용자 승인 대기, PLAN.md 참고
