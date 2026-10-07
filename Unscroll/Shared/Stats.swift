import Foundation

/// Totals for a time range, replayed from the event log.
struct UsageSummary {
    struct AppTotal: Hashable {
        var name: String
        var visits = 0
        var seconds = 0
    }

    var visits = 0
    var seconds = 0
    var walkAways = 0
    var passes = 0
    var nudges = 0
    var shields = 0
    var apps: [String: AppTotal] = [:]
    /// Longest single session: start date + seconds.
    var longest: (start: Date, seconds: Int, app: String)?

    var metres: Double { Odometer.metres(seconds: seconds) }

    var sortedApps: [AppTotal] {
        apps.values.sorted { ($0.seconds, $0.visits) > ($1.seconds, $1.visits) }
    }
}

struct Stats {
    let events: [LogEvent]
    let open: [String: OpenSession]
    let now: Date
    var calendar = Calendar.current

    /// Open sessions older than this are assumed to have lost their "closed" signal
    /// and are not counted live (we only count time we can vouch for).
    static let maxLiveSeconds = 2 * 3600

    init(events: [LogEvent], open: [String: OpenSession], now: Date = Date()) {
        self.events = events
        self.open = open
        self.now = now
    }

    static func load(now: Date = Date()) -> Stats {
        Stats(events: EventLog.readAll(), open: Settings.openSessions, now: now)
    }

    func dayInterval(_ date: Date) -> DateInterval {
        calendar.dateInterval(of: .day, for: date) ?? DateInterval(start: date, duration: 86_400)
    }

    /// Monday-start weeks, like the receipt ("29 SEP – 5 OCT").
    func weekInterval(containing date: Date) -> DateInterval {
        var cal = calendar
        cal.firstWeekday = 2
        return cal.dateInterval(of: .weekOfYear, for: date) ?? DateInterval(start: date, duration: 7 * 86_400)
    }

    func summary(_ interval: DateInterval, includeLive: Bool = true) -> UsageSummary {
        var s = UsageSummary()
        func bump(_ app: String?, visits: Int = 0, seconds: Int = 0) {
            let name = app ?? "Unknown"
            var total = s.apps[name] ?? UsageSummary.AppTotal(name: name)
            total.visits += visits
            total.seconds += seconds
            s.apps[name] = total
        }

        for e in events {
            switch e.type {
            case .open:
                guard interval.contains(e.ts) else { continue }
                s.visits += 1
                bump(e.app, visits: 1)
            case .close:
                let seconds = e.seconds ?? 0
                let start = e.ts.addingTimeInterval(-Double(seconds))
                guard seconds > 0, interval.contains(start) else { continue }
                s.seconds += seconds
                bump(e.app, seconds: seconds)
                if seconds > (s.longest?.seconds ?? 0) {
                    s.longest = (start, seconds, e.app ?? "Unknown")
                }
            case .walkAway:
                if interval.contains(e.ts) { s.walkAways += 1 }
            case .passUsed:
                if interval.contains(e.ts) { s.passes += 1 }
            case .nudgeShown:
                if interval.contains(e.ts) { s.nudges += 1 }
            case .shieldShown:
                if interval.contains(e.ts) { s.shields += 1 }
            case .shieldClose, .threshold, .setting:
                break
            }
        }

        if includeLive {
            for session in open.values where interval.contains(session.start) {
                let live = Int(now.timeIntervalSince(session.start))
                guard live > 0, live <= Stats.maxLiveSeconds else { continue }
                s.seconds += live
                bump(session.app, seconds: live)
                if live > (s.longest?.seconds ?? 0) { s.longest = (session.start, live, session.app) }
            }
        }
        return s
    }

    var today: UsageSummary { summary(dayInterval(now)) }

    var yesterday: UsageSummary {
        let start = calendar.date(byAdding: .day, value: -1, to: dayInterval(now).start) ?? now
        return summary(dayInterval(start), includeLive: false)
    }

    /// Visits to `app` today (used for "Visit N").
    func visitsToday(app: String) -> Int {
        let day = dayInterval(now)
        return events.filter {
            $0.type == .open && day.contains($0.ts)
                && ($0.app ?? "").caseInsensitiveCompare(app) == .orderedSame
        }.count
    }

    /// Hour of day (0–23) with the most minutes over the last 7 days, once there
    /// are at least 3 days and 30 minutes of data. Nil otherwise: no guessing.
    func riskiestHour() -> Int? {
        let since = now.addingTimeInterval(-7 * 86_400)
        var byHour = [Int: Int]()
        var days = Set<Date>()
        for e in events where e.type == .close && e.ts >= since {
            let seconds = e.seconds ?? 0
            guard seconds > 0 else { continue }
            let start = e.ts.addingTimeInterval(-Double(seconds))
            byHour[calendar.component(.hour, from: start), default: 0] += seconds
            days.insert(calendar.startOfDay(for: start))
        }
        let total = byHour.values.reduce(0, +)
        guard days.count >= 3, total >= 30 * 60 else { return nil }
        return byHour.max { $0.value < $1.value }?.key
    }

    /// Snapshot written for widgets and the shield.
    func snapshot() -> DaySnapshot {
        let t = today
        var names = Set(Settings.trackedApps)
        names.formUnion(t.apps.keys)
        let apps = names.sorted().map { name -> DaySnapshot.AppDay in
            let total = t.apps[name] ?? UsageSummary.AppTotal(name: name)
            return DaySnapshot.AppDay(name: name, visits: total.visits, seconds: total.seconds,
                                      limitMinutes: Settings.limitMinutes(for: name))
        }
        let limitTotal = apps.isEmpty ? Settings.defaultLimit : apps.map(\.limitMinutes).reduce(0, +)
        return DaySnapshot(
            day: dayInterval(now).start, updated: now,
            totalVisits: t.visits, totalSeconds: t.seconds, walkAways: t.walkAways,
            apps: apps, yesterdaySeconds: yesterday.seconds, limitMinutesTotal: limitTotal,
            voice: Settings.voice, nudgesOn: Settings.nudgesOn
        )
    }
}

enum SnapshotStore {
    static let url = AppGroup.file("today.json")

    static func load() -> DaySnapshot {
        guard let data = try? Data(contentsOf: url),
              let snapshot = try? JSONDecoder().decode(DaySnapshot.self, from: data) else {
            return .empty()
        }
        return snapshot.current()
    }

    static func save(_ snapshot: DaySnapshot) {
        guard let data = try? JSONEncoder().encode(snapshot) else { return }
        try? data.write(to: url, options: .atomic)
    }
}
