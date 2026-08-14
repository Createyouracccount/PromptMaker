# LOOP_LOG.md — 개선 루프 원장

라운드/세션마다 최상단에 1개 항목 추가 (최신이 위). 형식: 날짜·라운드 / 완료 / 실측 증거 / 발견 문제 / 다음 인수 지점.
이 파일이 세션 간 인수인계의 단일 원장이다. 판정 기준은 GATES.md(동결), 단계 이력은 LOG.md.

---

## 2026-08-14 · R23 (심판 검증: R21·R22 주장 — 성립 3/3, 단 R21 주장 하향 정정)

- **심판 판정 (fresh-context, 반증 프레이밍, 수치 재계산·배선 확인·g19 재현 포함)**: C1(언어 A/B) 성립 / C2(라우팅 차등) 성립 / C3(의견형 보호) 성립
- **심판 부기 → 정직한 정정**: 언어 A/B에 **위치 편향 교락** — 6쌍 중 5쌍에서 먼저 생성된 A 위치가 승리, 배정은 균형(K/E 각 3회)이나 생성 순서와 위치가 완전 교락. n=6에서 "한국어 우세"와 "위치 편향"을 분리 불가. **R21 결론을 "한국어 우세 입증"에서 "영어 우세 근거 없음 → 한국어(현상) 유지"로 하향 정정** — 유지 결정 자체는 유효(영어 전환의 근거가 없으므로)
- **라우팅 A/B는 강건**: v2 승리 4건이 A위치 2회·B위치 2회로 분산 — 위치 편향으로 설명 불가, 결론 유지
- **기타 부기 기록**: 환경 문맥 누출(재작성기가 repo 문맥 흡수 — 평가 일반화 약화, 실사용에선 유익), C2 지연 근거는 eval 경로 간접 실측(hook.log 28s 타임아웃 3건이 방증), v1은 복원 템플릿, 단일 심판·단일 런·무유의성검정
- **방법론 개선 의무(이후 실험)**: 쌍대 실험은 생성 순서와 제시 위치를 독립 교차시킬 것(A/B 위치 무작위화 + 순서 역균형), 골든셋 평가는 repo 밖 중립 cwd에서 실행할 것
- **다음 인수 지점**: Phase 4 실사용 데이터 수집(수락/거부율), language-matched 메타 실험(위 방법론으로), PyPI 토큰 대기

## 2026-08-14 · R22 (라우팅 v2: intent별 가이던스 — 경로별 차등 적용)

- **문제(사용자 지적)**: intent를 분류만 하고 라우팅에 미사용 — 모델 축(4프로필)만 있고 작업 유형 축 없음
- **구현**: INTENT_RULES(fix/debug·build·research·refactor·docs·general 별 1줄 가이던스) — 재작성기가 intent 분류 후 해당 블록 적용. full·condensed 메타 양쪽 주입
- **쌍대 실측 (eval/ab_routing_results.json, 블라인드 심판·원문 보존)**: **v2 4승 / v1 1패 / 1무.** 승리 사유: 증상·재현·완료기준 구체화(g01), 실행 절차 명시(g05), 가정 태깅 개선(g16)
- **패배 분석(g19)**: 의견 요청("어떻게 생각해")을 build로 오분류 → 실행 과제로 변질. 보호 규칙 1줄 추가("의견·질문형은 답변·평가 과제로 유지") → g19 단건 재검증: general 분류·평가 과제 유지 확인
- **지연 트레이드오프 발견 → 경로별 차등**: intent 블록 포함 시 2/6이 28s 초과(v1은 0/6), 훅 청정 재측정에서도 2/3 캡 초과 → **훅(28s 캡)은 경량 메타(intent_routing=False) 유지, /pm·CLI·MCP(60s+ 예산)는 v2 적용.** 차등 적용 후 훅 2/2 성공(21.9s/24.6s — 같은 프롬프트가 라우팅 메타로는 같은 시간대에 타임아웃)
- **테스트**: lean/routed 분기 고정 3건 추가, 37/37 OK
- **한계(정직)**: 실험 n=6·재작성기 haiku 1종·느린 시간대 측정 혼재. intent 오분류 가능성 잔존(g13→fix로 분류됐으나 v2 승리)
- **다음 인수 지점**: 실사용 데이터(Phase 4)로 intent 분류 정확도·수락률 검증, language-matched 메타(영어 원문→영어 메타) 실험

## 2026-08-13 · R21 (메타프롬프트 언어 A/B — 한국어 유지 결정, 근거 확보)

- **문제 제기(사용자)**: 한국어 메타프롬프트/프로필이 최선이라는 근거 없음. 문헌은 혼재(기술 지시문은 영어 동등~우세 경향, 원어는 문화 맥락 과제에서 우세)
- **실험**: 골든셋 6건(다양한 intent), 한/영 condensed 메타 쌍대 비교. 같은 시간대 교차 실행(시간대 편차 통제), 블라인드 심판(A/B 배정 기록 후 해맹), 심판 원문 보존
- **실측 (eval/ab_meta_language_results.json)**: **한국어 4승 / 영어 2승 / 무 0.** 지연 K avg 20.8s vs E avg 27.6s. 언어 보존(한국어 출력) 양쪽 12/12. 영어 메타는 토큰 수도 이점 없음(849자 ≈ 한국어 440자와 유사 토큰)
- **분석**: 승패 사유는 메타 언어 자체보다 무단 가정 추가 여부(fidelity)가 지배 — 실행 간 편차가 언어 효과보다 클 수 있음. 즉 "영어가 낫다" 가설은 우리 데이터에서 기각, 한국어 유지
- **한계·개방 항목**: n=6, 재작성기 haiku 1종, 원문이 전부 한국어. 영어 원문 사용자의 경우 영어 메타가 나을 가능성 미검증 — 원문 언어에 메타 언어를 맞추는 language-matched 라우팅은 향후 과제
- **부수 발견**: claude -p가 cwd 컨텍스트를 재작성에 주입(g18에서 repo 언급) — 훅 실사용에선 사용자 프로젝트 맥락 반영이라 유익, 평가에선 노이즈로 기록
- **다음 인수 지점**: R22 라우팅 v2 — intent 분류를 실제 라우팅에 사용(유형별 가이던스 블록), 쌍대 실측 후 채택

## 2026-08-12 · R19~R20 (사용자 승인 반영: 스킵 기준 완화 + Phase 3 MCP 서버 — 게이트 3/3 PASS)

- **사용자 승인 (4건)**: ① Phase 3 착수 ② 스킵 기준 <10→<6토큰 ③ PyPI 배포 ④ Windows는 "미검증 명시 유지". GATES.md에 개정 이력 2건 기록(동결 규칙 준수 — 사용자 승인으로만 변경)
- **R19 (스킵 기준)**: pm_hook <6토큰 적용. **실측**: "배포 자동화 하고싶어 도와줘"(7토큰) 훅 E2E → 17.2s 재작성 성공(구 기준에선 스킵되던 케이스), 회귀 테스트 추가 28/28 OK
- **R20 (MCP 서버, G3-1~3)**: promptmaker/mcp_server.py — stdio 개행 구분 JSON-RPC 2.0, 의존성 0, initialize/tools/list/tools/call/ping. `promptmaker-mcp` 엔트리포인트(깨끗한 venv 실측). 프로토콜 오프라인 테스트 6건 포함 34/34 OK
- **실측 증거**: runs/mcp_g31_roundtrip.txt(3왕복 원문, tools/call 실호출 포함) / runs/mcp_g32_claude_client.txt(독립 클라이언트 claude -p가 서버 스폰·호출, fable-5 산문 재작성 수신)
- **심판 판정 (fresh-context, 반증 프레이밍, 직접 재실행 포함)**: **G3-1 PASS / G3-2 PASS / G3-3 PASS — Phase 3 게이트 3/3.** 심판이 프로토콜 왕복·독립 클라이언트 호출·테스트 34건을 직접 재실행해 확인
- **심판 부기 → 조치**: ① R19·R20 원장 기록(본 항목) ② README 상태 갱신(같은 커밋) ③ [의무] 향후 MCP 클라이언트 증거는 --output-format stream-json으로 도구 호출 트랜스크립트까지 캡처 ④ [경미·기록만] initialize가 클라이언트 protocolVersion 에코 — 엄밀한 버전 협상 아님
- **다음 인수 지점**: PyPI 배포(승인됨, 자격증명 확인 필요), Cursor 실기기 검증(사용자 확인 항목), Phase 4(사용 데이터 기반 개선)

## 2026-08-12 · R18 (설치 화면 사용자 언어화 + 플랫폼 명시 — 루프 종료 라운드)

- **발굴**: install.sh 출력이 내부 연구 용어(G2-3·심판 3차·LOOP_LOG R7)를 신규 설치자에게 노출, README에 플랫폼·Python 요구사항 불명
- **완료**: 설치 문구를 사용자 언어로 교체(동작 설명 + 15~20초·28초 fail-open), README 요구사항에 Python 3.10+·macOS/Linux 검증·Windows 미검증 명시
- **실측**: install.sh 재실행 출력 확인, 테스트 27/27 OK
- **루프 종료 판정**: R8~R18 총 11라운드로 세션 처리 가능 백로그 소진 — 잔여는 전부 사용자 결정 필요(스킵 기준 재검토=동결 게이트 연관, Phase 3 MCP 게이트 초안 승인, PyPI 배포 여부, Windows 지원 여부). 선순환 체계(발굴→수정→실측→커밋→원장)는 PROMPT.md 재개 블록으로 다음 세션에서 재가동 가능
- **다음 인수 지점**: 사용자 승인 대기 항목 처리 후 Phase 3 착수

## 2026-08-12 · R17 (타임아웃 재시도 버그 수정)

- **발굴(버그)**: rewrite 재시도 except 절에 subprocess.TimeoutExpired 누락 — 타임아웃이 재시도를 우회하고 원시 트레이스백 노출 (훅은 fail-open이라 무사, CLI·/pm 경로 노출). CLI는 최종 RuntimeError도 미포획
- **완료**: except 절에 TimeoutExpired 추가, CLI에 RuntimeError → "재작성 실패: ..." + rc=1
- **실측**: 오프라인 테스트 2건 신설(call_claude 몽키패치) — 타임아웃 1회 후 성공 시 2회 호출·정상 결과 / 소진 시 RuntimeError. 전체 27/27 OK
- **다음 인수 지점**: 세션 처리 가능 백로그 사실상 소진 — 다음 라운드 신규 발굴 없으면 종료 보고(사용자 승인 대기: 스킵 기준, Phase 3 MCP 게이트)

## 2026-08-12 · R16 (/pm 백엔드 응답성 — 축약 메타 + 60s 캡)

- **발굴**: pm_command.py가 전체 메타(R7 실측 avg 41.4s·max 58.3s) + timeout=180·retries=1 — 인라인 대기 경로인데 최악 ~6분 블로킹 가능
- **완료**: `rewrite(..., retries=1, timeout=60, concise=True)`로 전환(훅과 동일한 검증된 경로), `__import__('time')` 인라인 제거
- **실측**: `time python3 scripts/pm_command.py "결제 모듈 리팩토링..."` → 30.9s, 유효 JSON([가정] 표기 포함). 최악 상한 ~2×60s로 확정. 오프라인 테스트 25/25 OK
- **다음 인수 지점**: 사용자 승인 대기 2건(스킵 기준, Phase 3 MCP 게이트) — 세션 처리 가능 백로그 소진 여부 다음 라운드 판정

## 2026-08-12 · R15 (루브릭 v2로 골든셋 전체 재평가 — 혼용 금지 해소)

- **완료**: R13 루브릭(조사 지시 예외)으로 골든셋 20건 전체 재평가 (`eval/run_eval.py --workers 5`, 백그라운드)
- **실측**: total=20 ok=20 errors=0 / verdict better 20-same 0-worse 0 / clarity 5.00·fidelity 4.80·actionability 5.00 / 프로필 차이 5/5. results.json 갱신(before는 git 이력에 보존)
- **정직성 주의**: 재작성도 재실행됐으므로 fidelity 4.10→4.80 전체를 루브릭 효과로 귀속 불가 — 격리 실측은 R13(동일 재작성본 4건 중 3건 4→5)이 근거
- **다음 인수 지점**: 사용자 승인 대기 2건(스킵 기준 재검토, Phase 3 MCP 게이트) 외 세션 처리 가능 백로그 소진 접근 — 다음 라운드는 신규 발굴(코드 품질·이식성) 또는 소진 시 종료 보고

## 2026-08-12 · R14 (오프라인 유닛 테스트 신설 — 회귀 안전망)

- **발굴**: repo에 유닛 테스트 전무 — 루프가 커밋을 계속 쌓는 구조인데 회귀 안전망이 없음
- **완료**: tests/test_offline.py (stdlib unittest, LLM 호출·네트워크 없음) — parse_json_output(펜스·주변 텍스트·실패), resolve_profile 별칭, build_meta_prompt(full/concise 길이 불변식 <700자), normalize_model([1m] 접미사·mythos→fable), 감지 우선순위(transcript>settings, local>project), 훅 스킵 규칙(슬래시·#raw·#rawdata 오탐·단문·장문), estimate_tokens(한/영 제수·단어 하한). pm_hook은 하이픈 경로라 importlib 로드
- **실측**: `python3 -m unittest discover tests` → 25/25 OK (0.003s)
- **다음 인수 지점**: 백로그 — (선택) 신 루브릭 골든셋 전체 재평가, 스킵 기준·Phase 3 게이트는 사용자 승인 대기

## 2026-08-12 · R13 (심판 루브릭에 조사 지시 예외 명문화 — 백로그 해소)

- **발굴**: 엔진 재작성 규칙은 "조사 지시는 가정 아님(표시 불요)"인데 심판 fidelity 루브릭에는 이 예외가 없어 규칙-루브릭 불일치 — 실제로 g01·g05·g11·g19 등이 조사 절차 추가를 이유로 fidelity 4점
- **완료**: JUDGE_PROMPT fidelity 기준에 조사 지시 예외 명문화
- **실측**: 기존 재작성본 4건 재심판(재작성 재실행 없음 — 루브릭 효과만 격리) → g01·g05·g11 fidelity 4→5(사유가 정확히 조사 지시 인정으로 바뀜), g19는 별개 사유(의견 요청→보고서로 범위 팽창)로 4 유지 — 예외 과잉 적용 아님. verdict 4/4 better 유지. 심판 원문 runs/rejudge_r13.json 보존(R7 의무 이행)
- **주의**: results.json의 기존 fidelity 평균(4.10)은 구 루브릭 기준 — 신 루브릭 전체 재평가 전까지 혼용 금지
- **다음 인수 지점**: 백로그 — 스킵 기준(사용자 승인 대기), Phase 3 MCP 초안 승인 대기, (선택) 신 루브릭으로 골든셋 전체 재평가

## 2026-08-12 · R12 (claude CLI 미설치 시 친절한 에러)

- **발굴**: `claude` 바이너리가 PATH에 없으면 FileNotFoundError 원시 트레이스백 노출 — 재시도 루프도 못 잡는 예외라 신규 사용자가 원인(설치·로그인)을 알 수 없음
- **완료**: `ClaudeCLINotFoundError`(비재시도, Exception 직속 — retry except 절 비포획) 신설, call_claude에서 FileNotFoundError 변환, CLI에서 한 줄 안내 + rc=1
- **실측**: `env PATH=/usr/bin:/bin python3 -m promptmaker.cli "..."` → 트레이스백 없이 "오류: `claude` CLI를 찾을 수 없습니다..." + rc=1. 훅 경로는 기존 fail-open이 전 예외 포획이라 영향 없음
- **다음 인수 지점**: 백로그 계속 — 심판 루브릭 조사 지시 예외 명문화, 스킵 기준(사용자 승인 대기), Phase 3 MCP 초안 승인 대기

## 2026-08-12 · R11 (README 온보딩 — clone→pip install 경로)

- **발굴**: README 사용법이 연구 폴더 내부 실행 기준 — GitHub 방문자의 clone→설치→실행 경로 부재
- **완료**: Quick Start(clone + `pip install .` + install.sh) 신설, 사용법을 설치된 `promptmaker` 명령 기준으로 갱신, `--concise` 반영
- **실측**: venv에 재설치 후 `promptmaker --help`로 문서화한 플래그(-m/--json/--concise) 전부 존재 확인
- **다음 인수 지점**: R8~R10 항목의 백로그 계속 (스킵 기준 재검토는 사용자 승인 대기)

## 2026-08-12 · R8~R10 (GitHub 공개 + 배포 품질 라운드)

- **공개 전 정리**: 개인 절대경로 3곳 제거 — pm.md는 `__PROMPTMAKER_ROOT__` placeholder + install.sh sed 치환으로 전환(하드코딩 경로는 이식성 버그이기도 했음). 재설치 실측으로 치환 동작 확인. 크리덴셜 스캔 결과 없음. `.gitignore`에 runs/hook.log·pm_command.log 추가(런타임 로그는 사용자 프롬프트 포함 가능 — 커밋 금지)
- **공개**: https://github.com/Createyouracccount/PromptMaker (public, main). 이후 라운드는 1문제=1커밋으로 푸시
- **R8**: MIT LICENSE 추가 + pyproject license 필드 (공개 repo 라이선스 부재는 타인 사용 불가 문제)
- **R9**: 패키징 버그 수정 — package-data가 `profiles/*.md`만 포함해 pip 설치본에서 concise 모드(훅 경로) 깨짐 → `profiles/condensed/*.md` 추가. **실측**: 깨끗한 venv에 pip 설치 → condensed 4종 포함·`build_meta_prompt(concise=True)` 동작·`promptmaker --version` 엔트리포인트 확인
- **R10**: 백로그 해소 — CLI에 `--concise` 플래그 노출. **실측**: `--concise --json` E2E 정상 출력(intent=fix, 유효 JSON)
- **다음 인수 지점**: 지속 루프 계속 — 남은 백로그: <10토큰 스킵 기준 재검토(게이트 연관— 사용자 승인 필요), 심판 루브릭 조사 지시 예외, README 신규 사용자 온보딩(영문 병기·요구사항), Phase 3 MCP 게이트 초안 승인 대기

## 2026-08-11 · R7 (메타프롬프트 축약으로 G2-3(c) 해소 — Phase 2 전 게이트 PASS)

- **가설**: 미시도 레버였던 입력 크기 축소가 지연 병목일 것 (기존: 출력 상한·플래그는 효과 없음)
- **완료**: CONDENSED_TEMPLATE + `profiles/condensed/*.md` 4종(각 ~250자) 신설, `build_meta_prompt(concise=True)`, 훅은 `retries=0, timeout=28, concise=True` (28s 캡 초과 시 fail-open 무개입)
- **실측 증거**:
  - 축약 메타(316자) 4회: 14.8~21.9s (avg 19.5) vs 전체 메타(2425자) 같은 창 4회: 15.3~58.3s (avg 41.4) — **입력 크기가 병목 맞음**
  - 훅 E2E 6샘플: 성공 5건 14.5~19.2s, 1건 28.0s 캡 fail-open (hook.log `ERROR (28.0s): TimeoutExpired` — 캡 작동 확인)
  - 품질 회귀 검사(축약 메타, 골든셋 4건): **verdict 4/4 better 유지**, clarity·fidelity 동일, actionability는 g01·g05에서 5→4 경미 하락 (심판 지적 반영해 "동등"이 아니라 "verdict 동등·actionability 경미 하락"으로 정정 기록). 축약 4건의 심판 원문 미저장은 실수 — 이후 라운드는 원문 보존 의무
- **심판 3차 판정 (G2-3 한정, 독립 재실행 2회 포함)**: **(a) PASS (b) PASS (c) PASS — G2-3 전체 PASS.** 독립 실측 16.93s/18.39s, JSON 기계 검증 통과. (c)의 fail-open 인정 근거: 완료 주체는 훅 프로세스이며 (b)가 무개입을 유효 동작으로 규정, 기능 경로도 7/8건 <20s로 실증
- **Phase 2 종합: 게이트 5/5 PASS** (G2-1·G2-2·G2-4·G2-5는 2차, G2-3은 3차). 사용자 결정 3안은 (b)에 준하는 결과를 키 없이 달성해 해소 — 훅 자동 모드 정식화
- **다음 인수 지점**: Phase 3 게이트는 GATES.md에 미정의(동결 파일이라 세션이 추가 불가) — 사용자 승인용 초안을 최종 보고에 제시. 잔여 백로그: <10토큰 스킵 기준 재검토(실제 타깃 프롬프트 스킵), 심판 루브릭에 조사 지시 예외 명문화, CLI 경로에도 concise 옵션 노출

## 2026-08-11 · R6 (심판 2차 판정 + 잔존 지적 수정 — Phase 2 종료)

- **심판 2차 판정 (fresh-context, 반증 프레이밍, LLM 재실행 0회)**:
  G2-1 **PASS** / G2-2 **PASS** / G2-3 **FAIL**((c) 30s만 미달, (a)(b) 충족) / G2-4 **PASS**((a) 코드 확인, (b) 지적 5→1~2 감소 검증 — 심판은 g05를 엄격 판독 시 잔존으로 봄) / G2-5 **PASS**. "G2-3(c) 미달 보고의 정직성: 정직(PASS)"
- **심판 잔존 지적 → 즉시 수정**: ① install.sh 스니펫에 "30s 게이트 미달·사용자 결정 대기" 명기 ② pm_hook docstring "<4 words"→"<10 tokens" 정정 ③ `#raw` 뒤 구두점 매칭(`#raw\b`, `#rawdata`는 여전히 비스킵 — 3케이스 재검증 통과)
- **미수정(정보로 기록)**: <10토큰 스킵이 실제 타깃 프롬프트("배포 자동화 하고싶어 도와줘"=7토큰)도 걸러냄 — 게이트 문구에는 부합하나 행동 트레이드오프. 게이트 재검토 대상으로 사용자에게 보고
- **Phase 2 종합**: 게이트 4/5 PASS. **G2-3(c)만 미달** — claude -p 경로의 구조적 지연(기동+API 편차)으로 30s 안정 충족 불가. 기준 완화 없이 사용자 결정 3안 제시: (a) 게이트를 "설정 timeout(60s) 내"로 개정 (b) Phase 3에서 직접 API 호출(ANTHROPIC_API_KEY 필요, 기동 ~11s 제거) (c) 훅 자동 모드를 실험 기능으로 유지하고 /pm을 기본 경로로
- **다음 인수 지점**: 사용자 결정 반영 → Phase 3 (MCP 서버 for Cursor / 직접 API 옵션 / 심판 루브릭에 조사 지시 예외 명문화 / <10토큰 기준 재검토)

## 2026-08-11 · R5 (심판 1차 FAIL 항목 수정)

- **심판 1차 판정**: G2-1 PASS / G2-2 PASS / G2-3 FAIL / G2-4 FAIL / G2-5 PASS(보완 요망). 지적 F-1~F-7 (전문은 세션 보고에 첨부)
- **수정 완료**:
  - F-2 → run_eval.py `_call_judge`: 심판 호출에 재시도 2회 + 필수 필드 검증 (실측된 실패 모드 g19 잘림·g02 필드 누락을 정확히 커버)
  - F-3 → 단문 스킵을 <10토큰 추정으로 변경 (한국어 chars/2, 영어 chars/4, 단어 수 하한)
  - F-7b → `#raw` 정확 토큰 매칭 (`#rawdata` 오탐 해소, 실측 확인)
  - F-7c → 훅 내부 재작성 호출 timeout 40s 캡 (훅 예산 60s 내 fail-open 보장)
  - F-6 → R3/R3.1 원장 기재 (아래 항목)
- **지연 개선 시도 (P1) 실측**:
  - MCP 로딩 차단(`--strict-mcp-config --mcp-config '{}'`): 32.0s → 25.5s 단발 확인 → 엔진 반영
  - `--bare`: 로그인 자격증명까지 스킵되어 사용 불가 (rc=1 "Not logged in")
  - `--disable-slash-commands --disallowedTools "*"`: 역효과 (avg 56.9s) → 폐기
  - 동일 시간대 대조 4회 (현행 구성): 25.1 / 31.7 / 32.9 / 34.7s — avg 31.1, max 34.7
- **판정 (정직하게)**: **G2-3(c) 30s 기준은 claude -p 경로로 충족 불가** (p50≈30s, 시점 편차 ±10s). GATES는 동결이므로 완화하지 않음 → "미달 + 사용자 결정 대기"로 보고. 선택지: (a) 게이트를 "훅 timeout 설정값(60s) 내"로 개정 승인 (b) Phase 3에서 직접 API 호출(키 필요, 기동비 제거) (c) 훅 자동 모드를 실험 기능으로 표기하고 /pm을 기본 경로로
- **다음 인수 지점**: g07·g09 재실행 판독 → 심판 2차

## 2026-08-11 · R3.1 (fidelity [가정] 예시 보강)

- **완료**: 메타프롬프트에 [가정] 규칙 위반/준수 구체 예시 추가 → g05·g13 재실행
- **실측 증거**: g13 지적 해소 ("추가한 가정을 명시적으로 표시해 왜곡 없이") / g05는 조사 지시 추가에 대한 지적 잔존 — 우리 규칙상 조사 지시는 가정 아님(규칙-심판 인식 경계), 문서화로 대응 / subset 지적 2/5(before) → 1/5(after)
- **발견 문제**: 심판이 "조사 지시 추가"도 fidelity 감점 사유로 봄 — 재작성 규칙과 심판 루브릭 간 정의 불일치 (Phase 3에서 루브릭에 조사 지시 예외 명문화 검토)

## 2026-08-11 · R3 (fidelity [가정] 강제 + 프로필 차이 재검증)

- **완료**: 메타프롬프트에 "[가정] 없는 무단 구체화는 실패" 규칙 추가, subset 5건(g05·g12·g13·g18·g19) 재실행 (before 스냅샷: eval/results_phase1_snapshot.json)
- **실측 증거**: 전건 verdict=better 유지 / **프로필 차이 5/5 달성** (Phase 1의 g05 실패가 프로필 규칙 8 추가로 해소 — "A는 단계 나열 없이 목표·제약만, B는 체크리스트·번호 단계") / fidelity 수치는 4.0 불변 (심판이 구체화 존재 시 4점을 상한으로 두는 경향)
- **다음 인수 지점**: R3.1 예시 보강

## 2026-08-11 · R2.1 (재귀 가드 검증 + /pm 증거 + 지연 재측정)

- **완료**: PROMPTMAKER_ACTIVE 환경변수 재귀 가드 (pm_hook.py + pm_command.py), pm_command.py 실행 로깅, 재작성문 700자 상한
- **실측 증거**:
  - 재귀 가드 작동: hook.log `02:04:17 skip (recursion-guard)` → 외부 재작성 정상 완료 (`02:05:03 rewrote`)
  - /pm 재작성 경로 통과: pm_command.log `02:09:24 ok target=fable-5 raw='readme 파일 하나 써줘'` + 응답이 재작성 지침 구조(요구사항 질문 4종) 반영
  - 700자 상한 후 지연: 46.5~49.6s — **개선 없음** (생성 길이가 병목이 아님; 단 동시 평가 부하 중 측정으로 과대 가능)
- **발견 문제**: P1 지속 — 훅 지연 31~50s, timeout 60 내이나 여유 부족. 근본 대책은 claude -p 기동비(10.9s 실측) 제거 = 직접 API 호출 옵션 (Phase 3 백로그)
- **다음 인수 지점**: R3.1 fidelity 재검증 판독 → R4 심판

## 2026-08-11 · R2 (Claude Code 통합: /pm + 훅)

- **완료**: pm_hook.py(UserPromptSubmit, additionalContext 주입, 스킵 4종: 슬래시/#raw/단문/800자 초과, fail-open + runs/hook.log), pm.md(/pm 커맨드, ~/.claude/commands 설치 완료), pm_command.py(백엔드), install.sh
- **실측 증거**:
  - 훅 직접 호출: 유효 JSON 출력, additionalContext 357자, **42.9s 소요**
  - CLI 기동 오버헤드 실측: 사소한 프롬프트도 10.9s (고정비) → 재작성 생성이 ~32s
  - E2E(headless, scratch 프로젝트): 훅 31.3s에 재작성 주입, 응답이 재작성 지침(병목 특정·수치 측정)을 반영함 확인
  - /pm E2E(headless): 빈 디렉토리에서 재작성된 요구사항 질문 구조로 응답 확인
- **발견 문제**:
  - **P1 지연**: 훅 재작성 31~43s — 기본 훅 타임아웃(30s) 초과 위험. 대응: settings 스니펫에 timeout 60 명시. 근본 개선 백로그: claude -p 대신 직접 API 호출(기동 10.9s 제거), 훅용 축약 메타프롬프트
  - **P2 첫 프롬프트 모델 감지 한계**: transcript에 assistant 레코드가 없는 세션 첫 프롬프트에서는 --model 플래그를 감지할 수 없어 settings 기본 모델로 폴백 (2번째 프롬프트부터 정확). 실측으로 확인, 문서화로 대응
  - **P3 훅 재귀 (심각)**: 훅이 띄운 내부 claude -p가 같은 프로젝트 설정을 상속받아 훅을 재트리거. "800자 초과 스킵"이 우연히 막아줌 → PROMPTMAKER_ACTIVE 환경변수 가드 추가로 구조적 차단 (검증 진행 중)
- **다음 인수 지점**: 재귀 가드 검증 → /pm 로깅 증거 확보 → R3 fidelity 재평가 판독

## 2026-08-11 · R1 (모델 자동 감지 실측)

- **완료**: promptmaker/detect.py — 감지 우선순위: 명시 인자 → transcript 마지막 assistant model → 프로젝트 settings → 사용자 settings → 기본값. normalize_model이 "[1m]" 접미사·전체 ID(claude-haiku-4-5-20251001)를 프로필 스템으로 정규화
- **실측 증거** (scratch 프로젝트 + stdin 덤프 훅):
  - 훅 입력 JSON 필드: session_id, transcript_path, cwd, prompt_id, permission_mode, hook_event_name, prompt — **model 필드 없음 확정**
  - transcript JSONL의 assistant 레코드에 message.model="claude-haiku-4-5-20251001" 존재 확인
  - ~/.claude/settings.json에 "model": "claude-fable-5[1m]" 존재 확인
- **다음 인수 지점**: R2 통합 구현

## 2026-08-11 · R0 (루프 인프라 구축)

- **완료**: failbench PROMPT.md v2 방법론 검토 → PromptMaker에 이식. GATES.md(동결 기준) + LOOP_LOG.md(이 파일) + PROMPT.md(재요청 블록) 신설
- **다음 인수 지점**: R1 — 모델 자동 감지 실측 (G2-1)
