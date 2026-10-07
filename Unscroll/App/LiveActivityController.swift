import ActivityKit
import Foundation

enum LiveActivityController {
    static func startOrUpdate(app: String, state: SessionAttributes.ContentState) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }
        let content = ActivityContent(state: state, staleDate: nil)

        // One session at a time: switching straight from one app to another ends the old pill.
        for activity in Activity<SessionAttributes>.activities where activity.attributes.appName != app {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
        if let existing = Activity<SessionAttributes>.activities.first(where: { $0.attributes.appName == app }) {
            await existing.update(content)
        } else {
            _ = try? Activity.request(attributes: SessionAttributes(appName: app), content: content, pushType: nil)
        }
    }

    static func end(app: String) async {
        for activity in Activity<SessionAttributes>.activities where activity.attributes.appName == app {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }

    static func endAll() async {
        for activity in Activity<SessionAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }
}
