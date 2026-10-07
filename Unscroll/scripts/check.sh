#!/usr/bin/env bash
# Compile every target without signing and report errors/warnings.
# Usage: scripts/check.sh [full|lite]
set -uo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-full}"
SPEC="project.yml"; [[ "$MODE" == "lite" ]] && SPEC="project-lite.yml"
export DEVELOPMENT_TEAM="${DEVELOPMENT_TEAM:-}"

command -v xcodegen >/dev/null || { echo "xcodegen missing: brew install xcodegen"; exit 1; }
xcodegen --spec "$SPEC" --quiet || exit 1
mkdir -p build

LOG="build/check-$MODE.log"
xcodebuild -project Unscroll.xcodeproj -scheme Unscroll -configuration Debug \
  -destination 'generic/platform=iOS' -derivedDataPath build/check \
  CODE_SIGNING_ALLOWED=NO build > "$LOG" 2>&1
STATUS=$?

ERRORS=$(grep -E "^/.*: error:" "$LOG" | sort -u)
WARNINGS=$(grep -E "^/.*: warning:" "$LOG" | sort -u)
echo "── $SPEC: errors $(printf "%s" "$ERRORS" | grep -c . ), warnings $(printf "%s" "$WARNINGS" | grep -c . )"
[[ -n "$ERRORS" ]] && printf "%s\n" "$ERRORS"
[[ -n "$WARNINGS" ]] && printf "%s\n" "$WARNINGS"
[[ $STATUS -ne 0 ]] && { echo "Build failed. Full log: $LOG"; tail -20 "$LOG"; }
exit $STATUS
