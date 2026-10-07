import DeviceActivity
import FamilyControls
import Foundation
import ManagedSettings

/// App-side Screen Time controls. All of this is behind `FeatureFlags.screenTime`.
enum ScreenTimeManager {
    static var isAuthorized: Bool {
        FeatureFlags.screenTime && AuthorizationCenter.shared.authorizationStatus == .approved
    }

    static func requestAuthorization() async -> Bool {
        guard FeatureFlags.screenTime else { return false }
        do {
            try await AuthorizationCenter.shared.requestAuthorization(for: .individual)
        } catch {
            return false
        }
        return isAuthorized
    }

    /// (Re)starts the daily monitor with 10 min, 20 min and limit thresholds per app.
    static func apply(_ config: ScreenTimeConfig) throws {
        guard FeatureFlags.screenTime else { return }
        config.save()
        let center = DeviceActivityCenter()
        center.stopMonitoring([.daily])
        Shields.clearAll()
        guard !config.limits.isEmpty else { return }

        var events: [DeviceActivityEvent.Name: DeviceActivityEvent] = [:]
        for (index, limit) in config.limits.enumerated() {
            let apps: Set<ApplicationToken> = [limit.token]
            let rungs: [(ThresholdKind, Int)] = [(.t10, 10), (.t20, 20), (.limit, limit.minutes)]
            for (kind, minutes) in rungs where kind == .limit || minutes < limit.minutes {
                events[kind.name(index)] = DeviceActivityEvent(
                    applications: apps, threshold: DateComponents(minute: minutes))
            }
        }
        let schedule = DeviceActivitySchedule(
            intervalStart: DateComponents(hour: 0, minute: 0, second: 0),
            intervalEnd: DateComponents(hour: 23, minute: 59, second: 59),
            repeats: true
        )
        try center.startMonitoring(.daily, during: schedule, events: events)
    }

    /// Debug: shield every chosen app right now, as if the limit were hit.
    static func shieldNow() {
        for limit in ScreenTimeConfig.load().limits { Shields.add(limit.token) }
    }

    static func clearShields() {
        Shields.clearAll()
    }
}
