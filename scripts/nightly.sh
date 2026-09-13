#!/bin/bash
# 매일 23:00 — 로컬 화면(http://127.0.0.1:4000)을 그 시각 GitHub main 으로 갱신한다.
#
# 낮에 파일을 고쳐도 4000 번 화면은 바뀌지 않는다. main 을 받아 개발일지를 쪼개고, 빌드하고,
# 검사를 통과한 것만 live/ 로 옮긴다. 검사가 실패하면 어제 화면을 그대로 둔다(설계 2026-09-13 §3.1).
# 커밋·push 는 하지 않는다 — 배포는 GitHub 의 23:00 예약 실행이 한다.
#
# 작업 폴더가 ~/Documents 밖(~/.local/share/thehorn)인 이유: macOS 는 launchd 가 띄운 프로세스가
# ~/Documents 를 읽지 못하게 막는다("Operation not permitted"). 그래서 이 스크립트는 자기 전용
# 클론을 따로 두고, 사람이 작업하는 클론은 건드리지 않는다.
#
#   nightly.sh            전용 클론을 origin/main 으로 맞추고 반영 (launchd 가 부른다)
#   nightly.sh <트리>     그 트리를 그대로 반영 (설치 직후 첫 화면용 — 받지 않는다)
set -uo pipefail
export PATH="$HOME/.rbenv/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export LANG=ko_KR.UTF-8

BASE="$HOME/.local/share/thehorn"
URL="https://github.com/masterlesscompany/thehorn.masterlesscompany.com.git"
LIVE="$BASE/live"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }

if [[ $# -ge 1 ]]; then
  SRC="$(cd "$1" && pwd)"
  log "시작 — 지정한 트리 $SRC"
else
  SRC="$BASE/repo"
  log "시작 — GitHub main"
  [[ -d "$SRC/.git" ]] || git clone --quiet "$URL" "$SRC" || { log "✗ 클론 실패 — 어제 화면 유지"; exit 1; }
  # 전용 클론이라 아무도 여기서 작업하지 않는다 — 원격과 똑같이 맞춘다.
  git -C "$SRC" fetch --quiet origin main && git -C "$SRC" reset --quiet --hard origin/main \
    || { log "✗ main 받기 실패 — 어제 화면 유지"; exit 1; }
  log "main — $(git -C "$SRC" log --oneline -1)"
fi

cd "$SRC" || exit 1
[[ -f scripts/split_devlog.py && -d jekyll ]] || { log "✗ 사이트 파일이 없다(jekyll/ · split_devlog.py) — 어제 화면 유지"; exit 1; }
python3 scripts/split_devlog.py || { log "✗ 개발일지 쪼개기 실패 — 어제 화면 유지"; exit 1; }
( cd jekyll && bundle exec jekyll build --quiet -d "$TMP/site" ) || { log "✗ 빌드 실패 — 어제 화면 유지"; exit 1; }
python3 scripts/check_site.py --site "$TMP/site" || { log "✗ 검사 실패 — 어제 화면 유지"; exit 1; }

mkdir -p "$LIVE"
rsync -a --delete "$TMP/site/" "$LIVE/"
log "✓ 반영 — http://127.0.0.1:4000"
