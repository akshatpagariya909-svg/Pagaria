import DeviceActivity
import FamilyControls
import Foundation
import ManagedSettings

/// Compile-time feature flag. `SCREEN_TIME` is set by project-screentime.yml; the
/// lite build (project-lite.yml) leaves it out when Family Controls can't be signed.
enum FeatureFlags {
    #if SCREEN_TIME
    static let screenTime = true
    #else
    static let screenTime = false
    #endif
}

/// Apps chosen with FamilyActivityPicker and their daily limits. Shared with the
/// monitor and shield extensions through the App Group.
struct ScreenTimeConfig: Codable {
    struct Limit: Codable, Hashable {
        var token: ApplicationToken
        var minutes: Int
    }

    var selection = FamilyActivitySelection()
    var limits: [Limit] = []

    private static let key = "screenTimeConfig"

    static func load() -> ScreenTimeConfig {
        guard let data = AppGroup.defaults.data(forKey: key),
              let config = try? JSONDecoder().decode(ScreenTimeConfig.self, from: data) else {
            return ScreenTimeConfig()
        }
        return config
    }

    func save() {
        AppGroup.defaults.set(try? JSONEncoder().encode(self), forKey: Self.key)
    }

    func index(of token: ApplicationToken) -> Int? {
        limits.firstIndex { $0.token == token }
    }

    func minutes(for token: ApplicationToken) -> Int {
        limits.first { $0.token == token }?.minutes ?? Settings.defaultLimit
    }

    /// Keeps `limits` in sync with the picker: new apps get the default limit.
    mutating func syncLimits() {
        let tokens = selection.applicationTokens
        limits.removeAll { !tokens.contains($0.token) }
        for token in tokens where index(of: token) == nil {
            limits.append(Limit(token: token, minutes: Settings.defaultLimit))
        }
    }
}

extension DeviceActivityName {
    static let daily = DeviceActivityName("unscroll.daily")

    static func pass(_ index: Int) -> DeviceActivityName {
        DeviceActivityName("unscroll.pass.\(index)")
    }
}

/// Event names encode what happened and for which app: "t10.2", "t20.2", "limit.2", "pass.2".
enum ThresholdKind: String {
    case t10, t20, limit, pass

    func name(_ index: Int) -> DeviceActivityEvent.Name {
        DeviceActivityEvent.Name("\(rawValue).\(index)")
    }

    static func parse(_ name: DeviceActivityEvent.Name) -> (ThresholdKind, Int)? {
        let parts = name.rawValue.split(separator: ".")
        guard parts.count == 2, let kind = ThresholdKind(rawValue: String(parts[0])),
              let index = Int(parts[1]) else { return nil }
        return (kind, index)
    }
}

enum Shields {
    static let store = ManagedSettingsStore(named: ManagedSettingsStore.Name("unscroll"))

    static func add(_ token: ApplicationToken) {
        var current = store.shield.applications ?? []
        current.insert(token)
        store.shield.applications = current
    }

    static func remove(_ token: ApplicationToken) {
        var current = store.shield.applications ?? []
        current.remove(token)
        store.shield.applications = current.isEmpty ? nil : current
    }

    static func clearAll() {
        store.shield.applications = nil
    }

    /// Re-arms the shield after 5 more minutes of use of `token` (a "pass").
    /// DeviceActivity schedules must be at least 15 minutes long, so the interval
    /// runs from now to the end of the day and the 5-minute usage event re-shields.
    static func scheduleReturn(of token: ApplicationToken, index: Int, now: Date = Date()) throws {
        let cal = Calendar.current
        let start = cal.dateComponents([.hour, .minute, .second], from: now)
        var end = DateComponents(hour: 23, minute: 59, second: 59)
        if let endOfDay = cal.date(bySettingHour: 23, minute: 59, second: 59, of: now),
           endOfDay.timeIntervalSince(now) < 16 * 60 {
            // Too close to midnight for a 15-minute schedule: run past midnight.
            end = cal.dateComponents([.hour, .minute, .second], from: now.addingTimeInterval(16 * 60))
        }
        let schedule = DeviceActivitySchedule(intervalStart: start, intervalEnd: end, repeats: false)
        let event = DeviceActivityEvent(applications: [token], threshold: DateComponents(minute: 5))
        let center = DeviceActivityCenter()
        center.stopMonitoring([.pass(index)])
        try center.startMonitoring(.pass(index), during: schedule, events: [ThresholdKind.pass.name(index): event])
    }
}
