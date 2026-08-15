---
description: 요청을 현재 모델에 맞는 프롬프트로 재작성한 뒤 그 프롬프트로 수행
allowed-tools: Bash(python3:*)
---

## 재작성 결과

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pm_command.py "$ARGUMENTS"`

## 지시

1. 첫 출력으로 변경 요약(changes)을 한 줄로 사용자에게 보여준 뒤 작업을 시작하라. 생략하지 마라.
2. 위 "재작성 결과"의 rewritten_prompt를 사용자의 실제 요청으로 간주하고 그대로 수행하라.
3. 사용자에게 보이는 모든 응답은 원문 "$ARGUMENTS"와 같은 언어로 작성하라 (한국어 원문이면 한국어로).
4. [가정]으로 표시된 부분은 단정하지 말고 작업 중에 확인하라.
5. 재작성 결과가 에러이면 원문 "$ARGUMENTS"를 그대로 수행하라.
