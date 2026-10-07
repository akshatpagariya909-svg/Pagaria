import DeviceActivity
import Foundation
import ManagedSettings
import UserNotifications

/// Daily Screen Time monitor: 10 min and 20 min nudges, and a shield at the limit.
/// Also re-arms the shield when a "5 more minutes" pass runs out.
final class DeviceActivityMonitorExtension: DeviceActivityMonitor {
    override func intervalDidStart(for activity: DeviceActivityName) {
        super.intervalDidStart(for: activity)
        if activity == .daily {
            // New day: lift yesterday's shields. Passes reset by date automatically.
            Shields.clearAll()
        }
    }

    override func eventDidReachThreshold(_ event: DeviceActivityEvent.Name, activity: DeviceActivityName) {
        super.eventDidReachThreshold(event, activity: activity)
        guard let parsed = ThresholdKind.parse(event) else { return }
        let (kind, index) = parsed
        let config = ScreenTimeConfig.load()
        guard config.limits.indices.contains(index) else { return }
        let limit = config.limits[index]

        switch kind {
        case .limit, .pass:
            Shields.add(limit.token)
            EventLog.log(.threshold, level: NudgeLevel.shield.rawValue,
                         note: "\(kind == .pass ? "pass used up" : "limit \(limit.minutes) min reached"); shield on (Screen Time app #\(index + 1))")
            if kind == .pass {
                DeviceActivityCenter().stopMonitoring([activity])
            }
        case .t10, .t20:
            let level: NudgeLevel = kind == .t10 ? .notice : .nudge
            let minutes = kind == .t10 ? 10 : 20
            EventLog.log(.threshold, level: level.rawValue,
                         note: "\(minutes) min today (Screen Time app #\(index + 1))")
            guard Settings.nudgesOn else { return }
            EventLog.log(.nudgeShown, level: level.rawValue, note: "screen time \(minutes) min today")
            notify(level: level, minutes: minutes, seed: index + minutes)
        }
    }

    private func notify(level: NudgeLevel, minutes: Int, seed: Int) {
        let content = UNMutableNotificationContent()
        content.title = "Unscroll · \(minutes) min today"
        content.body = CopyBank.line(
            voice: Settings.voice, level: level, seed: seed,
            context: .init(visit: 0, app: "this app", elapsedSeconds: minutes * 60)
        )
        content.sound = nil
        content.threadIdentifier = "nudges"
        let request = UNNotificationRequest(identifier: "st-\(UUID().uuidString)", content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request)
    }
}
