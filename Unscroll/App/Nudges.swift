import Foundation
import UserNotifications

/// Silent local notifications for the 10- and 20-minute rungs. Never a sound.
enum Nudges {
    static func requestPermission() async -> Bool {
        // No .sound on purpose.
        (try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge])) ?? false
    }

    static func identifier(session: UUID, level: NudgeLevel) -> String {
        "nudge-\(session.uuidString)-\(level.rawValue)"
    }

    static func schedule(session: UUID, level: NudgeLevel, app: String, body: String, after delay: TimeInterval) async {
        let content = UNMutableNotificationContent()
        content.title = "Unscroll · \(app)"
        content.body = body
        content.sound = nil
        content.interruptionLevel = .active
        content.threadIdentifier = "nudges"
        content.userInfo = ["level": level.rawValue, "app": app]
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: max(1, delay), repeats: false)
        let request = UNNotificationRequest(identifier: identifier(session: session, level: level),
                                            content: content, trigger: trigger)
        try? await UNUserNotificationCenter.current().add(request)
    }

    static func cancel(session: UUID) {
        let ids = NudgeLevel.allCases.map { identifier(session: session, level: $0) }
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: ids)
    }
}

/// Shows nudges as banners even while Unscroll itself is open (handy with the debug panel).
final class NotificationDelegate: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationDelegate()

    func userNotificationCenter(
        _ center: UNUserNotificationCenter, willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .list]
    }
}
