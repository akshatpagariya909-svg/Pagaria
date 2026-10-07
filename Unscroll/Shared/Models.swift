import Foundation

enum Voice: String, Codable, CaseIterable, Identifiable {
    case gentle, witty, blunt

    var id: String { rawValue }

    var title: String {
        switch self {
        case .gentle: return "Gentle"
        case .witty: return "Witty friend"
        case .blunt: return "Blunt"
        }
    }

    /// Sample shown on the voice picker (Onboarding.dc.html).
    var sample: String {
        switch self {
        case .gentle: return "\u{201C}Hey, it's been a while. Maybe a little break?\u{201D}"
        case .witty: return "\u{201C}Visit 25. We're basically roommates now.\u{201D}"
        case .blunt: return "\u{201C}38 minutes. Put it down.\u{201D}"
        }
    }
}

/// Rungs of the nudge ladder (NudgeLadder.dc.html).
enum NudgeLevel: Int, Codable, CaseIterable {
    case arrive = 0   // on open
    case notice = 1   // 10 min
    case nudge = 2    // 20 min
    case shield = 3   // limit hit

    var label: String {
        switch self {
        case .arrive: return "Arrive"
        case .notice: return "Notice"
        case .nudge: return "Nudge"
        case .shield: return "Shield"
        }
    }
}

enum EventType: String, Codable, CaseIterable {
    case open
    case close
    case nudgeShown
    case shieldShown
    case shieldClose      // "Close the app" tapped on the shield
    case passUsed
    case walkAway
    case threshold        // Screen Time usage threshold reached
    case setting          // experiment settings changed (nudges on/off, voice)
}

/// One row of validation data. Stored as JSON lines in the App Group.
struct LogEvent: Codable, Identifiable, Hashable {
    var id = UUID()
    var ts = Date()
    var type: EventType
    var app: String?
    var session: UUID?
    var visit: Int?
    var seconds: Int?
    var level: Int?
    var nudgesOn: Bool
    var voice: String
    var note: String?
}

/// A session that has been opened (via Shortcuts or the debug panel) and not closed yet.
struct OpenSession: Codable, Hashable {
    var id: UUID
    var app: String
    var start: Date
    var visit: Int
    /// Fire dates of the scheduled nudge notifications, keyed by level raw value.
    var nudgeFireDates: [Int: Date]
}

/// Small precomputed summary for widgets and the shield (they shouldn't parse the whole log).
struct DaySnapshot: Codable {
    struct AppDay: Codable, Hashable {
        var name: String
        var visits: Int
        var seconds: Int
        var limitMinutes: Int
    }

    var day: Date
    var updated: Date
    var totalVisits: Int
    var totalSeconds: Int
    var walkAways: Int
    var apps: [AppDay]
    var yesterdaySeconds: Int
    var limitMinutesTotal: Int
    var voice: Voice
    var nudgesOn: Bool

    static func empty(now: Date = Date()) -> DaySnapshot {
        DaySnapshot(
            day: Calendar.current.startOfDay(for: now), updated: now,
            totalVisits: 0, totalSeconds: 0, walkAways: 0, apps: [],
            yesterdaySeconds: 0, limitMinutesTotal: Settings.defaultLimitMinutes,
            voice: Settings.voice, nudgesOn: Settings.nudgesOn
        )
    }

    /// The snapshot is only valid for the day it was written. On a new day the
    /// old "today" becomes yesterday.
    func current(now: Date = Date()) -> DaySnapshot {
        let today = Calendar.current.startOfDay(for: now)
        if Calendar.current.isDate(day, inSameDayAs: today) { return self }
        var fresh = DaySnapshot.empty(now: now)
        if let yesterday = Calendar.current.date(byAdding: .day, value: -1, to: today),
           Calendar.current.isDate(day, inSameDayAs: yesterday) {
            fresh.yesterdaySeconds = totalSeconds
        }
        fresh.limitMinutesTotal = limitMinutesTotal
        return fresh
    }

    func app(named name: String?) -> AppDay? {
        guard let name else { return nil }
        return apps.first { $0.name.caseInsensitiveCompare(name) == .orderedSame }
    }
}
