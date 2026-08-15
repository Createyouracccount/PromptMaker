#!/bin/bash
# PromptTailor Claude Code 통합 설치
# - /pm 슬래시 커맨드를 ~/.claude/commands/에 복사
# - 훅 자동 모드는 설정 스니펫만 출력 (settings.json 자동 수정 안 함 — 옵트인)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.claude/commands"
sed "s|__PROMPT_TAILOR_ROOT__|$REPO_ROOT|g" "$REPO_ROOT/claude-code/commands/pm.md" > "$HOME/.claude/commands/pm.md"
echo "✓ /pm 커맨드 설치됨: ~/.claude/commands/pm.md"

cat <<EOF

[권장] auto 모드 사용 시: 프롬프트에 위험해 보이는 단어(예: "docker prune", "삭제")가 있으면
분류기가 /pm 백엔드 실행을 오탐 차단할 수 있습니다. ~/.claude/settings.json "permissions"에 추가:
  "allow": ["Bash(python3 $REPO_ROOT/scripts/pm_command.py:*)"]
(이 스크립트는 텍스트 재작성만 하며 프롬프트 내용을 실행하지 않습니다.)
EOF

cat <<EOF

[선택] 훅 자동 모드 — 프롬프트 제출 시 자동으로 재작성해 컨텍스트로 주입합니다.
재작성은 보통 15~20초이며, 28초 안에 끝나지 않으면 개입 없이 원문 그대로 전달됩니다.
활성화하려면 아래를 프로젝트 .claude/settings.json "hooks"에 추가:
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
