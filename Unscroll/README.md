# Unscroll (iOS MVP)

This MVP tests one question: **do constant, witty, visual nudges reduce doomscrolling better than a one-time Screen Time limit?**

- Week 1: nudges **off**. The app only counts, and the shield shows plain Screen Time-style text.
- Week 2: nudges **on**. You get the Live Activity, nudges at 10 and 20 minutes, and witty shield copy.

Every event is logged with the mode it happened in, so the CSV export splits cleanly by week.

## Run it (on the Mac, iPhone plugged in)

```bash
cd Unscroll
scripts/setup.sh          # checks Xcode, devicectl and Developer Mode, installs xcodegen,
                          # asks for your Team ID, then builds, installs and launches
scripts/check.sh          # optional: compiles all 5 targets unsigned and lists every error/warning
```

`setup.sh` builds from `project.yml` (all 5 targets). If signing fails because of
**Family Controls**, it rebuilds from `project-lite.yml` and tells you that the
Screen Time layer is off. To skip straight to the lite build, run `scripts/setup.sh lite`.
If the bundle ID is taken, run `UNSCROLL_BUNDLE_ID=com.akshat.unscroll.<you> scripts/setup.sh`.
The App Group follows the bundle ID automatically: `group.<bundle id>`.

## Layout

| Folder | Target | What's in it |
|---|---|---|
| `App/` | **Unscroll** | SwiftUI screens, App Intents, tracker, nudges, Live Activity control, CSV |
| `Widgets/` | **UnscrollWidgets** | Visits (small), Thumb odometer (medium), lock-screen circular and rectangular widgets, Live Activity / Dynamic Island |
| `Monitor/` | **UnscrollMonitor** | DeviceActivityMonitor: 10 min / 20 min / limit thresholds, shield at the limit |
| `ShieldConfig/` | **UnscrollShieldConfig** | Cream shield: visit count, rotating line, time today, passes |
| `ShieldAction/` | **UnscrollShieldAction** | Close / "5 more minutes" pass (3 a day) |
| `Shared/` | all | App Group, models, event log, settings, copy bank, odometer, stats |
| `SharedActivity/` | app + widgets | `SessionAttributes` (ActivityKit) |
| `SharedScreenTime/` | app + 3 extensions | Screen Time config, shield store, feature flag |

The `SCREEN_TIME` compilation flag (set only in `project-screentime.yml`) drives `FeatureFlags.screenTime`.
Liquid Glass (`.glassEffect`) is compiled in with Xcode 26 and used at runtime on iOS 26, only on the
tab bar, the Live Activity timer chip and buttons. Older systems fall back to materials.

`design/` holds the approved `.dc.html` mockups the UI was matched against.

## Checklist

### 1. What's installed
- [ ] The Unscroll app is on the phone and opens to onboarding.
- [ ] Widgets are in the widget gallery: Visits today, Thumb odometer, % of limit, Visits and time.
- [ ] Full build only: the monitor, shield configuration and shield action extensions (no icon; they run inside Screen Time).

### 2. Shortcuts automations (one pair per app)
In **Shortcuts › Automation › +**:
- [ ] **App › Instagram › Is Opened** (only that one ticked) › **Run Immediately**, with **Notify When Run** off › Next ›
      New Blank Automation › Add Action › **Log App Opened** › App name: `Instagram`
- [ ] **App › Instagram › Is Closed** › Run Immediately, Notify When Run off › **Log App Closed** › App name: `Instagram`
- [ ] Repeat for YouTube etc. The app name must match what you see in Unscroll (the
      "Copy app name" button in Settings › Shortcuts automations › Guide helps).

### 3. Permissions
- [ ] Notifications: **Allow**. Nudges are silent; the app never requests sound.
- [ ] Live Activities: on by default (Settings › Unscroll › Live Activities).
- [ ] Screen Time (full build): Limits › **Allow Screen Time access** › Choose apps › **Save and start monitoring**.
- [ ] If the first launch says "Untrusted Developer": Settings › General › **VPN & Device Management** › your Apple ID › Trust.

### 4. Test the whole ladder in 5 minutes (debug panel)
Go to Settings › Debug panel and make sure **Nudges** is on (Experiment section).
1. Turn on **Fast ladder**. Nudges fire at +10 s and +20 s instead of minutes, and the limit becomes 1 minute.
2. App name `Instagram` › **Simulate open**. The panel shows the banner line ("Visit 1. …"). Go to the
   Home Screen: the Dynamic Island shows a coloured dot, "visit 1" and a ticking timer. Long-press it to see
   the ring filling toward the 1-minute limit and the witty line. The lock screen shows the banner.
3. Wait. A silent notification arrives at +10 s (Notice), then another at +20 s (Nudge).
4. Within 60 s of the second one, go back to Unscroll › **Simulate close**. It reports "walk-away logged".
   The Live Activity ends, and Today shows 1 walk-away.
5. **Simulate open** again, wait about 90 s, then **Simulate close**. You get no walk-away, but the time counts.
6. Full build: **Shield now**, then open Instagram. You get the cream shield with "Visit N today", a line,
   the time and "5 more minutes · 3 passes left". Tap the pass: the shield lifts and comes back after
   5 more minutes of use. Next time, tap **Close the app**. **Clear shields** resets it.
7. Look at the widgets and the Week receipt (Share receipt exports a PNG). Settings › **Export test data (CSV)**.
8. Before the real experiment, turn **Fast ladder** off and tap **Reset all data**. Then turn **Nudges off** for week 1.

## Design decisions to know about
- **Numbers are always true.** If a session never got its "closed" signal, it's logged with 0 s, not guessed.
  Open sessions older than 2 h aren't counted live. The thumb odometer is minutes × 3.8 m (`Odometer.metresPerMinute`)
  and is labelled as an estimate everywhere. Landmark comparisons round **down** to the nearest half.
- **A walk-away** is a session that ends within 60 s of a 10/20-minute nudge, a Screen Time threshold nudge, or a shield.
  The "on open" banner doesn't count.
- **Lock-screen Live Activity:** the design's "Minute X in Instagram" line is built as "In Instagram · visit N"
  plus a ticking `minute` timer. A Live Activity can't change its text without an update, and only the timer
  counts up live.
- **Passes:** "5 more minutes" means 5 more minutes of *use*. It's a DeviceActivity usage threshold, because
  DeviceActivity schedules can't be shorter than 15 minutes.
- **The control week** keeps the same limits and passes and changes only the copy and nudges, so the
  comparison isolates the nudges.
- The shield can't read Shortcuts app names directly. It matches `localizedDisplayName` to the Shortcuts
  name, and without a match it shows "Limit reached" instead of a visit number.
