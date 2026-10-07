import Foundation

/// User settings shared by every target (App Group UserDefaults).
/// The SwiftUI screens bind to the same keys with @AppStorage(store: AppGroup.defaults).
enum Settings {
    enum Key {
        static let voice = "voice"
        static let nudgesOn = "nudgesOn"
        static let onboarded = "onboarded"
        static let defaultLimit = "defaultLimitMinutes"
        static let appLimits = "appLimits"
        static let trackedApps = "trackedApps"
        static let fastLadder = "debugFastLadder"
        static let openSessions = "openSessions"
        static let passesDay = "passesDay"
        static let passesUsed = "passesUsed"
    }

    static let defaultLimitMinutes = 45
    static let passesPerDay = 3

    private static var store: UserDefaults { AppGroup.defaults }

    static var voice: Voice {
        get { Voice(rawValue: store.string(forKey: Key.voice) ?? "") ?? .witty }
        set { store.set(newValue.rawValue, forKey: Key.voice) }
    }

    /// The experiment switch: week 1 = off (plain limit only), week 2 = on.
    static var nudgesOn: Bool {
        get { store.object(forKey: Key.nudgesOn) as? Bool ?? true }
        set { store.set(newValue, forKey: Key.nudgesOn) }
    }

    static var onboarded: Bool {
        get { store.bool(forKey: Key.onboarded) }
        set { store.set(newValue, forKey: Key.onboarded) }
    }

    /// Debug: nudges at +10 s / +20 s instead of +10 min / +20 min, limit = 1 min.
    static var fastLadder: Bool {
        get { store.bool(forKey: Key.fastLadder) }
        set { store.set(newValue, forKey: Key.fastLadder) }
    }

    static var defaultLimit: Int {
        get { (store.object(forKey: Key.defaultLimit) as? Int) ?? defaultLimitMinutes }
        set { store.set(newValue, forKey: Key.defaultLimit) }
    }

    /// Per-app daily limits for apps tracked through Shortcuts, keyed by app name.
    static var appLimits: [String: Int] {
        get { store.dictionary(forKey: Key.appLimits) as? [String: Int] ?? [:] }
        set { store.set(newValue, forKey: Key.appLimits) }
    }

    static func limitMinutes(for app: String) -> Int {
        if fastLadder { return 1 }
        return appLimits[app] ?? defaultLimit
    }

    /// App names seen from Shortcuts or added on the Limits screen.
    static var trackedApps: [String] {
        get { store.stringArray(forKey: Key.trackedApps) ?? [] }
        set { store.set(newValue, forKey: Key.trackedApps) }
    }

    static func track(_ app: String) {
        var apps = trackedApps
        if !apps.contains(where: { $0.caseInsensitiveCompare(app) == .orderedSame }) {
            apps.append(app)
            trackedApps = apps
        }
    }

    // MARK: Open sessions

    static var openSessions: [String: OpenSession] {
        get {
            guard let data = store.data(forKey: Key.openSessions) else { return [:] }
            return (try? JSONDecoder().decode([String: OpenSession].self, from: data)) ?? [:]
        }
        set {
            store.set(try? JSONEncoder().encode(newValue), forKey: Key.openSessions)
        }
    }

    static func resetAll() {
        for key in [Key.appLimits, Key.trackedApps, Key.openSessions, Key.passesDay, Key.passesUsed] {
            store.removeObject(forKey: key)
        }
    }
}

/// "5 more minutes" passes on the shield: 3 a day.
enum Passes {
    private static var store: UserDefaults { AppGroup.defaults }

    static func used(now: Date = Date()) -> Int {
        guard let day = store.object(forKey: Settings.Key.passesDay) as? Date,
              Calendar.current.isDate(day, inSameDayAs: now) else { return 0 }
        return store.integer(forKey: Settings.Key.passesUsed)
    }

    static func remaining(now: Date = Date()) -> Int {
        max(0, Settings.passesPerDay - used(now: now))
    }

    /// Returns false if there were no passes left.
    @discardableResult
    static func use(now: Date = Date()) -> Bool {
        let count = used(now: now)
        guard count < Settings.passesPerDay else { return false }
        store.set(Calendar.current.startOfDay(for: now), forKey: Settings.Key.passesDay)
        store.set(count + 1, forKey: Settings.Key.passesUsed)
        return true
    }
}
