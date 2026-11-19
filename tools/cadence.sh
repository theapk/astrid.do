#!/bin/bash
# astrid cadence launcher — reconcile loop + warehouse ship, as root, with
# Operator alert lane on drift transitions. Chat id + token come from
# /etc/astrid/* on the box (token 0600; the id is config, not code).
set -u
STATE=/var/lib/astrid/reconcile-state.json
LOG=/var/log/astrid-reconcile.log

mode="${1:-reconcile}"

alert() {  # $1 = text
  local tok pfx="ℹ️"
  case "$1" in *broken*) pfx="🚨";; *all-clear*) pfx="✅";; esac
  tok=$(head -1 "${ASTRID_ALERT_TOKEN:-/etc/astrid/tg-token}")
  curl -s -m 15 "https://api.telegram.org/bot${tok}/sendMessage" \
       -d chat_id="${ASTRID_ALERT_CHAT:?set ASTRID_ALERT_CHAT}" --data-urlencode "text=${pfx} astrid: $1" -o /dev/null
  echo "$(date -u +%FT%TZ) alert-sent($?): $1" >> "$LOG"
}

prev=""
[ -f "$STATE" ] && prev=$(python3 -c "import json;print(json.load(open('$STATE')).get('last_broken',''))")

if [ "$mode" = "ship" ]; then
  "${ASTRID_TOOLS:-$HOME/tools}/ship.py" >/dev/null 2>>"$LOG"
  rc=$?
  echo "$(date -u +%FT%TZ) ship-rc=$rc" >> "$LOG"
  if [ "$rc" -ne 0 ]; then
    [ "$prev" != "ship-fail" ] && alert "warehouse ship FAILED (rc=$rc)" && echo '{"last_broken":"ship-fail"}' > "$STATE"
  else
    [ "$prev" = "ship-fail" ] && alert "warehouse ship all-clear"
    echo '{"last_broken":false}' > "$STATE"
  fi
  exit $rc
fi

# reconcile
"${ASTRID_TOOLS:-$HOME/tools}/reconcile.py" "${ASTRID_CHARTER:-$HOME/charter/example.json}" > /var/lib/astrid/drift.json 2>>"$LOG"
rc=$?
sev=$(python3 -c "import json;print(json.load(open('/var/lib/astrid/drift.json'))['severity'])" 2>/dev/null || echo unknown)
summ=$(python3 -c "import json;print(json.load(open('/var/lib/astrid/drift.json'))['summary'][:220])" 2>/dev/null || echo unknown)
echo "$(date -u +%FT%TZ) reconcile rc=$rc sev=$sev" >> "$LOG"
if [ "$rc" -ne 0 ]; then
  if [ "$prev" != "true" ]; then
    alert "drift [broken] $sev — $summ"
    echo '{"last_broken":true}' > "$STATE"
    # chain: try the plan leg + gate (no auto-apply ever; verdict lands in the log)
    "${ASTRID_TOOLS:-$HOME/tools}/plan.py" /var/lib/astrid/drift.json /var/lib/astrid/plan.json >>"$LOG" 2>&1 \
      && "${ASTRID_TOOLS:-$HOME/tools}/gate.py" /var/lib/astrid/plan.json "${ASTRID_CHARTER:-$HOME/charter/example.json}" >>"$LOG" 2>&1
    echo "$(date -u +%FT%TZ) plan+gate attempted (verdict in log)" >> "$LOG"
  fi
else
  [ "$prev" = "true" ] && echo '{"last_broken":false}' > "$STATE" &&
    alert "reconcile all-clear" && exit 0
  echo '{"last_broken":false}' > "$STATE"
fi
exit $rc
