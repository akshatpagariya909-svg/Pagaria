import Foundation
import WidgetKit

/// The core mechanic: Shortcuts automations (or the debug panel) tell us when a
/// watched app opens and closes. Everything else hangs off these two calls.
enum Tracker {
    /// A walk-away is a session that ends within this many seconds of a nudge or shield.
    static let walkAwayWindow: TimeInterval = 60

    /// Nudge delays from session start. The debug "fast ladder" uses seconds instead.
    static func nudgeDelays() -> [NudgeLevel: TimeInterval] {
        Settings.fastLadder ? [.notice: 10, .nudge: 20] : [.notice: 10 * 60, .nudge: 20 * 60]
    }

    /// Logs an open and returns the line to show in the Shortcuts banner.
    @discardableResult
    static func appOpened(_ rawName: String, now: Date = Date()) async -> String {
        let app = clean(rawName)
        Settings.track(app)
        var open = Settings.openSessions

        // An earlier session that never got its "closed" signal: close it at 0 s so
        // we don't invent time we can't vouch for.
        if let stale = open[app] {
            EventLog.log(.close, app: app, session: stale.id, visit: stale.visit, seconds: 0,
                         note: "no close signal; time not counted", at: now)
            Nudges.cancel(session: stale.id)
        }

        let stats = Stats.load(now: now)
        let visit = stats.visitsToday(app: app) + 1
        let usedToday = stats.today.apps[app]?.seconds ?? 0
        let limitMinutes = Settings.limitMinutes(for: app)

        var session = OpenSession(id: UUID(), app: app, start: now, visit: visit, nudgeFireDates: [:])
        EventLog.log(.open, app: app, session: session.id, visit: visit, at: now)

        let voice = Settings.voice
        let context = CopyBank.Context(visit: visit, app: app, elapsedSeconds: 0)
        let line = CopyBank.line(voice: voice, level: .arrive, seed: visit, context: context)

        guard Settings.nudgesOn else {
            open[app] = session
            Settings.openSessions = open
            refresh()
            return "Logged visit \(visit) to \(app)."
        }

        EventLog.log(.nudgeShown, app: app, session: session.id, visit: visit,
                     level: NudgeLevel.arrive.rawValue, note: "open banner + Live Activity", at: now)

        for (level, delay) in nudgeDelays() {
            let fire = now.addingTimeInterval(delay)
            session.nudgeFireDates[level.rawValue] = fire
            let text = CopyBank.line(voice: voice, level: level, seed: visit,
                                     context: .init(visit: visit, app: app, elapsedSeconds: Int(delay)))
            await Nudges.schedule(session: session.id, level: level, app: app, body: text, after: delay)
        }
        open[app] = session
        Settings.openSessions = open

        let limitStart = now.addingTimeInterval(-Double(usedToday))
        let state = SessionAttributes.ContentState(
            visit: visit, sessionStart: now, limitStart: limitStart,
            limitEnd: limitStart.addingTimeInterval(Double(limitMinutes * 60)),
            limitMinutes: limitMinutes, line: line
        )
        await LiveActivityController.startOrUpdate(app: app, state: state)

        refresh()
        return line
    }

    static func appClosed(_ rawName: String, now: Date = Date()) async {
        let app = clean(rawName)
        var open = Settings.openSessions
        guard let session = open.removeValue(forKey: app) else {
            EventLog.log(.close, app: app, seconds: 0, note: "close without open", at: now)
            await LiveActivityController.end(app: app)
            refresh()
            return
        }
        Settings.openSessions = open

        let seconds = max(0, Int(now.timeIntervalSince(session.start)))
        EventLog.log(.close, app: app, session: session.id, visit: session.visit, seconds: seconds, at: now)

        // Nudges whose time has passed were delivered while the session was open.
        var lastNudge: (date: Date, level: Int)?
        for (level, fire) in session.nudgeFireDates.sorted(by: { $0.key < $1.key }) where fire <= now {
            EventLog.log(.nudgeShown, app: app, session: session.id, visit: session.visit,
                         level: level, note: "notification", at: fire)
            lastNudge = (fire, level)
        }
        Nudges.cancel(session: session.id)

        // Shields and Screen Time threshold nudges come from extensions, which can't
        // see app names reliably, so any of them in the last minute counts.
        let recent = EventLog.readAll().last { e in
            let isNudge = e.type == .shieldShown || e.type == .shieldClose
                || (e.type == .nudgeShown && (e.level ?? 0) >= NudgeLevel.notice.rawValue)
            return isNudge && e.ts >= session.start && now.timeIntervalSince(e.ts) <= walkAwayWindow
        }
        if let nudge = recent, nudge.ts > (lastNudge?.date ?? .distantPast) {
            lastNudge = (nudge.ts, nudge.level ?? NudgeLevel.shield.rawValue)
        }
        if let nudge = lastNudge, now.timeIntervalSince(nudge.date) <= walkAwayWindow {
            EventLog.log(.walkAway, app: app, session: session.id, visit: session.visit,
                         seconds: Int(now.timeIntervalSince(nudge.date)), level: nudge.level, at: now)
        }

        await LiveActivityController.end(app: app)
        refresh()
    }

    /// Rewrites the widget/shield snapshot and reloads widget timelines.
    static func refresh() {
        SnapshotStore.save(Stats.load().snapshot())
        WidgetCenter.shared.reloadAllTimelines()
    }

    static func resetAllData() async {
        for session in Settings.openSessions.values { Nudges.cancel(session: session.id) }
        await LiveActivityController.endAll()
        EventLog.reset()
        Settings.resetAll()
        refresh()
    }

    private static func clean(_ name: String) -> String {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "Unknown app" }
        // Reuse the existing spelling so "instagram" and "Instagram" are one app.
        return Settings.trackedApps.first { $0.caseInsensitiveCompare(trimmed) == .orderedSame } ?? trimmed
    }
}
