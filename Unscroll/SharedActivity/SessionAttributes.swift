import ActivityKit
import Foundation

/// Live Activity for one session in a watched app.
struct SessionAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var visit: Int
        var sessionStart: Date
        /// Ring range: starts at (sessionStart - time already used today) and ends when
        /// the per-app daily limit is reached, so `ProgressView(timerInterval:)` fills
        /// toward the limit with no updates needed.
        var limitStart: Date
        var limitEnd: Date
        var limitMinutes: Int
        var line: String
    }

    var appName: String
}

extension SessionAttributes.ContentState {
    /// Generous upper bound so `Text(timerInterval:)` keeps counting up.
    var timerRange: ClosedRange<Date> {
        sessionStart...sessionStart.addingTimeInterval(12 * 3600)
    }

    var limitRange: ClosedRange<Date> {
        limitStart...max(limitEnd, limitStart.addingTimeInterval(1))
    }
}
