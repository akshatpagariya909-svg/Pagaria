import SwiftUI
import UserNotifications

@main
struct UnscrollApp: App {
    @State private var model = AppModel()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        UNUserNotificationCenter.current().delegate = NotificationDelegate.shared
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(model)
                .tint(Palette.accent)
                .preferredColorScheme(.light)
        }
        .onChange(of: scenePhase) { _, phase in
            // Intents may have written data while we were in the background.
            if phase == .active { model.reload() }
        }
    }
}
