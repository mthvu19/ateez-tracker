#!/usr/bin/env bash
# Chay cap nhat lap lai trong $1 giay. Nguon mien phi moi gio; X them vao luot 10h va 18h (gio VN).
set -u
LIMIT=${1:-20400}
END=$((SECONDS + LIMIT))
git config user.name "ateez-tracker-bot"
git config user.email "actions@users.noreply.github.com"
LAST_X=""
while :; do
  git pull -q --rebase -X theirs origin main || true
  HOUR_VN=$(TZ=Asia/Ho_Chi_Minh date +%H)
  DAY_VN=$(TZ=Asia/Ho_Chi_Minh date +%F)
  SOURCES="kq,youtube,news"
  if { [ "$HOUR_VN" = "10" ] || [ "$HOUR_VN" = "18" ]; } && [ "$LAST_X" != "$DAY_VN-$HOUR_VN" ]; then
    SOURCES="$SOURCES,x"; LAST_X="$DAY_VN-$HOUR_VN"
  fi
  echo "=== $(date -u +%FT%TZ) nguon: $SOURCES"
  python -m tracker.run --sources "$SOURCES" || echo "luot chay loi, thu lai luot sau"
  git add docs/data state.json
  if ! git diff --cached --quiet; then
    git commit -q -m "data: cap nhat $(date -u +%Y-%m-%dT%H:%MZ)"
    git pull -q --rebase -X theirs origin main && git push -q || echo "push loi"
  fi
  # ngu den phut 17 cua gio tiep theo
  NOW_M=$((10#$(date -u +%M))); NOW_S=$((10#$(date -u +%S)))
  WAIT=$(( ((77 - NOW_M) % 60) * 60 - NOW_S )); [ $WAIT -le 60 ] && WAIT=$((WAIT + 3600))
  if [ $((SECONDS + WAIT)) -ge $END ]; then echo "het thoi gian vong lap"; break; fi
  sleep $WAIT
done
