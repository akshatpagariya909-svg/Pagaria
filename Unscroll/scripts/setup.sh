#!/usr/bin/env bash
# Unscroll: check the environment, build, install and launch on a cabled iPhone.
#
#   scripts/setup.sh            # full build; falls back to lite if Family Controls can't be signed
#   scripts/setup.sh lite       # skip the Screen Time targets
#   DEVELOPMENT_TEAM=ABCDE12345 scripts/setup.sh
#   UNSCROLL_BUNDLE_ID=com.akshat.unscroll2 scripts/setup.sh   # if the bundle ID is taken
set -uo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-auto}"
BUNDLE_ID="${UNSCROLL_BUNDLE_ID:-com.akshat.unscroll}"
mkdir -p build
bold() { printf "\n\033[1m%s\033[0m\n" "$*"; }
fail() { printf "\n\033[31m✗ %s\033[0m\n" "$*"; exit 1; }
ok()   { printf "\033[32m✓\033[0m %s\n" "$*"; }

# ── 1. Xcode ────────────────────────────────────────────────────────────────
bold "1. Xcode"
xcodebuild -version || fail "Xcode not found. Install it from the App Store, open it once, then run: sudo xcode-select -s /Applications/Xcode.app"
XCODE_MAJOR=$(xcodebuild -version | awk '/^Xcode/{split($2,v,"."); print v[1]}')
if [[ "${XCODE_MAJOR:-0}" -ge 26 ]]; then ok "Xcode $XCODE_MAJOR: Liquid Glass enabled on iOS 26"; else ok "Xcode $XCODE_MAJOR: Liquid Glass compiled out (needs Xcode 26); materials used instead"; fi

# ── 2. iPhone ───────────────────────────────────────────────────────────────
bold "2. iPhone"
xcrun devicectl list devices || fail "devicectl failed. Xcode 15 or later is required."
xcrun devicectl list devices --json-output build/devices.json >/dev/null 2>&1 || true
DEVICE_INFO=$(/usr/bin/python3 - <<'PY'
import json, sys
try:
    devices = json.load(open("build/devices.json"))["result"]["devices"]
except Exception:
    sys.exit(0)
def score(d):
    c = d.get("connectionProperties", {})
    return (c.get("transportType") == "wired", c.get("tunnelState") == "connected")
phones = [d for d in devices if d.get("hardwareProperties", {}).get("platform") == "iOS"]
if not phones:
    sys.exit(0)
d = sorted(phones, key=score, reverse=True)[0]
dp, hp, cp = d.get("deviceProperties", {}), d.get("hardwareProperties", {}), d.get("connectionProperties", {})
print("|".join([d.get("identifier", ""), hp.get("udid", ""), dp.get("name", "iPhone"),
                str(dp.get("developerModeStatus", "unknown")), str(dp.get("osVersionNumber", "?")),
                str(cp.get("transportType", "?"))]))
PY
)
[[ -z "$DEVICE_INFO" ]] && fail "No iPhone found. Plug it in, unlock it, tap 'Trust This Computer', then run this again."
IFS='|' read -r DEVICE_ID UDID DEVICE_NAME DEV_MODE IOS_VERSION TRANSPORT <<< "$DEVICE_INFO"
ok "$DEVICE_NAME · iOS $IOS_VERSION · $TRANSPORT · udid $UDID"
IOS_MAJOR=${IOS_VERSION%%.*}
[[ "${IOS_MAJOR:-0}" =~ ^[0-9]+$ && "$IOS_MAJOR" -lt 17 ]] && fail "Unscroll needs iOS 17 or later (this phone has $IOS_VERSION)."

if [[ "$DEV_MODE" != "enabled" ]]; then
  cat <<MSG

Developer Mode is '$DEV_MODE' on $DEVICE_NAME. To turn it on:
  1. On the iPhone: Settings › Privacy & Security › Developer Mode › On.
     (If the switch isn't there, open Xcode › Window › Devices and Simulators
      with the phone plugged in; the switch appears after that.)
  2. Tap Restart. After the reboot, unlock and tap 'Turn On' in the alert.
  3. Run this script again.
MSG
  fail "Developer Mode is off."
fi
ok "Developer Mode is on"

# ── 3. XcodeGen ─────────────────────────────────────────────────────────────
bold "3. XcodeGen"
if ! command -v xcodegen >/dev/null; then
  command -v brew >/dev/null || fail "Homebrew is missing. Install it from https://brew.sh, then run: brew install xcodegen"
  brew install xcodegen || fail "brew install xcodegen failed"
fi
ok "xcodegen $(xcodegen --version 2>/dev/null | tail -1)"

# ── 4. Team ID ──────────────────────────────────────────────────────────────
bold "4. Apple Development Team ID"
TEAM="${DEVELOPMENT_TEAM:-$(cat .team 2>/dev/null || true)}"
if [[ -z "$TEAM" ]]; then
  echo "Find it at developer.apple.com/account › Membership details, or in"
  echo "Xcode › Settings › Accounts › (your Apple ID) › the team list (10 characters)."
  read -r -p "Team ID: " TEAM
fi
TEAM=$(echo "$TEAM" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')
[[ "$TEAM" =~ ^[A-Z0-9]{10}$ ]] || fail "'$TEAM' doesn't look like a Team ID (10 letters/digits)."
echo "$TEAM" > .team
export DEVELOPMENT_TEAM="$TEAM"
ok "Team $TEAM · bundle $BUNDLE_ID · App Group group.$BUNDLE_ID"

# ── 5. Build ────────────────────────────────────────────────────────────────
build() {
  local spec="$1" name="$2"
  bold "5. Build ($name: $spec)"
  rm -rf Unscroll.xcodeproj
  xcodegen --spec "$spec" || return 1
  xcodebuild -project Unscroll.xcodeproj -scheme Unscroll -configuration Debug \
    -destination "id=$UDID" -derivedDataPath build/device \
    -allowProvisioningUpdates -allowProvisioningDeviceRegistration \
    DEVELOPMENT_TEAM="$TEAM" UNSCROLL_BUNDLE_ID="$BUNDLE_ID" \
    build > "build/xcodebuild-$name.log" 2>&1
  local status=$?
  grep -E "^/.*: (error|warning):" "build/xcodebuild-$name.log" | sort -u
  echo "warnings: $(grep -E '^/.*: warning:' "build/xcodebuild-$name.log" | sort -u | grep -c .)"
  return $status
}

DISABLED=""
if [[ "$MODE" == "lite" ]]; then
  build project-lite.yml lite || { tail -30 build/xcodebuild-lite.log; fail "Lite build failed (log: build/xcodebuild-lite.log)."; }
  DISABLED="yes"
elif build project.yml full; then
  ok "Full build succeeded (Screen Time on)"
else
  if grep -qiE "error:.*family.?controls" build/xcodebuild-full.log && [[ "$MODE" == "auto" ]]; then
    printf "\n\033[33m! Family Controls couldn't be signed for team %s.\033[0m\n" "$TEAM"
    grep -iE "error:.*family.?controls" build/xcodebuild-full.log | sort -u | head -5
    echo "  Falling back to the lite build: Screen Time targets OFF."
    build project-lite.yml lite || { tail -30 build/xcodebuild-lite.log; fail "Lite build failed too (log: build/xcodebuild-lite.log)."; }
    DISABLED="yes"
  else
    tail -40 build/xcodebuild-full.log
    cat <<MSG

Signing/build help:
  • "No Account for Team": open Xcode › Settings › Accounts and sign in with your Apple ID.
  • "bundle identifier is not available": it's taken by another team. Run:
        UNSCROLL_BUNDLE_ID=com.akshat.unscroll.\$(whoami) scripts/setup.sh
  • "Personal development teams ... do not support ...": that capability needs the paid
    Apple Developer Program. Try: scripts/setup.sh lite
  • Device not registered: open Xcode › Window › Devices and Simulators once with the phone plugged in.
MSG
    fail "Build failed (log: build/xcodebuild-full.log)."
  fi
fi

APP="build/device/Build/Products/Debug-iphoneos/Unscroll.app"
[[ -d "$APP" ]] || fail "Built app not found at $APP"

# ── 6. Install + launch ─────────────────────────────────────────────────────
bold "6. Install and launch"
xcrun devicectl device install app --device "$DEVICE_ID" "$APP" || fail "Install failed. Is the phone unlocked?"
ok "Installed"
if ! xcrun devicectl device process launch --device "$DEVICE_ID" "$BUNDLE_ID"; then
  cat <<MSG

Launch was blocked. If the phone says "Untrusted Developer":
  Settings › General › VPN & Device Management › Developer App › (your Apple ID) › Trust,
  then tap the Unscroll icon (or run: xcrun devicectl device process launch --device $DEVICE_ID $BUNDLE_ID)
MSG
else
  ok "Launched on $DEVICE_NAME"
fi

bold "Done"
if [[ -n "$DISABLED" ]]; then
  echo "Screen Time layer DISABLED in this build: no DeviceActivityMonitor, no ShieldConfiguration,"
  echo "no ShieldAction, no Limits picker, no shield or passes. Everything else works."
else
  echo "All 5 targets installed: app, widgets + Live Activity, monitor, shield configuration, shield action."
fi
