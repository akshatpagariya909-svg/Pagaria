import AppIntents
import Foundation

/// Run from a Shortcuts personal automation: "When Instagram is Opened → Log App Opened".
/// Runs in the background; conforming to LiveActivityIntent lets it start the Live Activity.
struct LogAppOpenedIntent: AppIntent, LiveActivityIntent {
    static let title: LocalizedStringResource = "Log App Opened"
    static let description = IntentDescription("Counts a visit to a watched app and starts the Unscroll session timer.")
    static let openAppWhenRun = false

    @Parameter(title: "App name", default: "Instagram")
    var appName: String

    static var parameterSummary: some ParameterSummary {
        Summary("Log \(\.$appName) opened")
    }

    init() {}

    init(appName: String) {
        self.appName = appName
    }

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let line = await Tracker.appOpened(appName)
        return .result(dialog: "\(line)")
    }
}

/// "When Instagram is Closed → Log App Closed".
struct LogAppClosedIntent: AppIntent, LiveActivityIntent {
    static let title: LocalizedStringResource = "Log App Closed"
    static let description = IntentDescription("Ends the Unscroll session for a watched app and cancels pending nudges.")
    static let openAppWhenRun = false

    @Parameter(title: "App name", default: "Instagram")
    var appName: String

    static var parameterSummary: some ParameterSummary {
        Summary("Log \(\.$appName) closed")
    }

    init() {}

    init(appName: String) {
        self.appName = appName
    }

    func perform() async throws -> some IntentResult {
        await Tracker.appClosed(appName)
        return .result()
    }
}
