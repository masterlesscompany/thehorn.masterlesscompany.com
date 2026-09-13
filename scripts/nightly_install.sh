#!/bin/bash
# 밤 11시 로컬 반영을 이 맥에 설치한다. 제거: scripts/nightly_install.sh --uninstall
#
# launchd 는 ~/Documents 를 읽지 못하므로 실행 파일과 작업 폴더를 ~/.local/share/thehorn 에 둔다.
# 설치 직후에는 이 트리로 한 번 반영해 둔다 — 그다음부터는 매일 23:00 에 GitHub main 으로 갱신된다.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$HOME/.local/share/thehorn"
AGENTS="$HOME/Library/LaunchAgents"
LABELS=(com.masterlesscompany.thehorn.serve com.masterlesscompany.thehorn.nightly)

for l in "${LABELS[@]}"; do
  launchctl bootout "gui/$(id -u)/$l" 2>/dev/null || true
  rm -f "$AGENTS/$l.plist"
done
if [[ "${1:-}" == "--uninstall" ]]; then
  echo "제거했다. 작업 폴더는 남겨 두었다: $BASE (지우려면 rm -rf)"; exit 0
fi

mkdir -p "$AGENTS" "$HOME/Library/Logs" "$BASE/live"
install -m 755 "$REPO/scripts/nightly.sh" "$BASE/nightly.sh"
"$BASE/nightly.sh" "$REPO"

for l in "${LABELS[@]}"; do
  sed -e "s#__BASE__#$BASE#g" -e "s#__HOME__#$HOME#g" "$REPO/ops/launchd/$l.plist" > "$AGENTS/$l.plist"
  plutil -lint -s "$AGENTS/$l.plist"
  launchctl bootstrap "gui/$(id -u)" "$AGENTS/$l.plist"
done
echo "설치했다 — 매일 23:00 반영 · http://127.0.0.1:4000 · 로그 ~/Library/Logs/thehorn-nightly.log"
echo "스크립트를 고치면 설치를 다시 돌린다(실행 파일이 $BASE 에 복사돼 있다)."
