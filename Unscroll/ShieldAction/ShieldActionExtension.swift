import ManagedSettings

/// "Close the app" closes. "5 more minutes" spends a pass, lifts the shield, and
/// re-arms it after 5 more minutes of use.
final class ShieldActionExtension: ShieldActionDelegate {
    override func handle(action: ShieldAction, for application: ApplicationToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        switch action {
        case .primaryButtonPressed:
            EventLog.log(.shieldClose, level: NudgeLevel.shield.rawValue, note: "Close the app")
            completionHandler(.close)

        case .secondaryButtonPressed:
            guard Passes.use() else {
                completionHandler(.none)
                return
            }
            var note = "\(Passes.remaining()) left"
            if let index = ScreenTimeConfig.load().index(of: application) {
                do {
                    try Shields.scheduleReturn(of: application, index: index)
                } catch {
                    note += "; re-shield not scheduled: \(error.localizedDescription)"
                }
            }
            EventLog.log(.passUsed, level: NudgeLevel.shield.rawValue, note: note)
            Shields.remove(application)
            completionHandler(.defer)

        @unknown default:
            completionHandler(.close)
        }
    }

    override func handle(action: ShieldAction, for webDomain: WebDomainToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        completionHandler(.close)
    }

    override func handle(action: ShieldAction, for category: ActivityCategoryToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        completionHandler(.close)
    }
}
