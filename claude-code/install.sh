#!/bin/bash
# PromptMaker Claude Code 통합 설치
# - /pm 슬래시 커맨드를 ~/.claude/commands/에 복사
# - 훅 자동 모드는 설정 스니펫만 출력 (settings.json 자동 수정 안 함 — 옵트인)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.claude/commands"
sed "s|__PROMPTMAKER_ROOT__|$REPO_ROOT|g" "$REPO_ROOT/claude-code/commands/pm.md" > "$HOME/.claude/commands/pm.md"
echo "✓ /pm 커맨드 설치됨: ~/.claude/commands/pm.md"

cat <<EOF

[선택] 훅 자동 모드 — 축약 메타프롬프트로 재작성 14.5~19.2s 실측 (내부 28s 캡, 초과 시 무개입 통과).
G2-3 게이트 PASS (심판 3차, LOOP_LOG.md R7). 아래를 프로젝트 .claude/settings.json "hooks"에 추가:
{
  "hooks": {
    "UserPromptSubmit": [
      {"hooks": [{"type": "command",
                  "command": "python3 $REPO_ROOT/claude-code/hooks/pm_hook.py",
                  "timeout": 60}]}
    ]
  }
}
우회: 프롬프트에 #raw 포함 시 재작성 없이 원문 그대로 전달됩니다.
EOF
