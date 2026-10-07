import SwiftUI
import WidgetKit

struct SnapshotEntry: TimelineEntry {
    let date: Date
    let snapshot: DaySnapshot
}

/// Widgets read the small snapshot the app writes after every event, and are reloaded
/// by `WidgetCenter.reloadAllTimelines()` whenever an intent writes data.
struct SnapshotProvider: TimelineProvider {
    func placeholder(in context: Context) -> SnapshotEntry {
        SnapshotEntry(date: Date(), snapshot: .sample)
    }

    func getSnapshot(in context: Context, completion: @escaping (SnapshotEntry) -> Void) {
        let snapshot = SnapshotStore.load()
        let useSample = context.isPreview && snapshot.totalVisits == 0
        completion(SnapshotEntry(date: Date(), snapshot: useSample ? .sample : snapshot))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<SnapshotEntry>) -> Void) {
        let now = Date()
        var entries = [SnapshotEntry(date: now, snapshot: SnapshotStore.load())]
        // Roll over cleanly at midnight even if the app doesn't run.
        if let midnight = Calendar.current.nextDate(after: now, matching: DateComponents(hour: 0, minute: 0), matchingPolicy: .nextTime) {
            entries.append(SnapshotEntry(date: midnight, snapshot: SnapshotStore.load().current(now: midnight)))
        }
        completion(Timeline(entries: entries, policy: .after(now.addingTimeInterval(15 * 60))))
    }
}

extension DaySnapshot {
    /// Gallery/placeholder only (matches the mockup). Never shown as real data.
    static let sample = DaySnapshot(
        day: Calendar.current.startOfDay(for: Date()), updated: Date(),
        totalVisits: 25, totalSeconds: 108 * 60, walkAways: 9,
        apps: [.init(name: "Instagram", visits: 25, seconds: 108 * 60, limitMinutes: 45)],
        yesterdaySeconds: 65 * 60, limitMinutesTotal: 160, voice: .witty, nudgesOn: true
    )

    var metres: Double { Odometer.metres(seconds: totalSeconds) }
    var yesterdayMetres: Double { Odometer.metres(seconds: yesterdaySeconds) }
    var limitMetres: Double { Double(limitMinutesTotal) * Odometer.metresPerMinute }
    var limitFraction: Double { Double(totalSeconds) / Double(max(1, limitMinutesTotal * 60)) }
}

/// Short lines for the small widget. They describe, never count, so they can't be wrong.
enum WidgetCopy {
    static func visits(_ visits: Int, voice: Voice) -> String {
        let tier: Int
        switch visits {
        case 0: tier = 0
        case 1...5: tier = 1
        case 6...15: tier = 2
        default: tier = 3
        }
        let lines: [Voice: [String]] = [
            .gentle: ["Nothing yet today. Nice.", "A light day so far.", "A busy day for your thumb.", "Maybe a calmer evening?"],
            .witty: ["Zero. Who even are you?", "Just popping in, huh?", "Getting to know each other.", "Roommates at this point."],
            .blunt: ["Zero. Keep it there.", "Keep it low.", "That's a lot of check-ins.", "Too many. Cut it."],
        ]
        return lines[voice]?[tier] ?? ""
    }
}

extension View {
    func monoCaps(_ size: CGFloat = 11, color: Color) -> some View {
        self.font(Typo.mono(size)).textCase(.uppercase).tracking(size * 0.06).foregroundStyle(color)
    }
}
