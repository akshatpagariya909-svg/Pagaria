import Foundation

/// Everything every target shares lives in one App Group.
/// The identifier comes from Info.plist (`UnscrollAppGroup`), which XcodeGen
/// fills from the `UNSCROLL_APP_GROUP` build setting.
enum AppGroup {
    static let id: String =
        Bundle.main.object(forInfoDictionaryKey: "UnscrollAppGroup") as? String
        ?? "group.com.akshat.unscroll"

    static let defaults: UserDefaults = UserDefaults(suiteName: id) ?? .standard

    /// Shared container. Falls back to the app's own Documents folder if the
    /// App Group entitlement is missing, so the app still runs (data just
    /// won't reach the widgets/extensions).
    static let containerURL: URL = {
        if let url = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: id) {
            return url
        }
        return FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }()

    static func file(_ name: String) -> URL {
        containerURL.appendingPathComponent(name)
    }
}
