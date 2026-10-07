import ManagedSettings
import ManagedSettingsUI
import UIKit

/// Shield.dc.html: warm cream, today's visit count as the title, a line that changes
/// every time you come back, and "5 more minutes · N passes left".
final class ShieldConfigurationExtension: ShieldConfigurationDataSource {
    override func configuration(shielding application: Application) -> ShieldConfiguration {
        make(appName: application.localizedDisplayName, token: application.token)
    }

    override func configuration(shielding application: Application, in category: ActivityCategory) -> ShieldConfiguration {
        make(appName: application.localizedDisplayName, token: application.token)
    }

    override func configuration(shielding webDomain: WebDomain) -> ShieldConfiguration {
        make(appName: webDomain.domain, token: nil)
    }

    override func configuration(shielding webDomain: WebDomain, in category: ActivityCategory) -> ShieldConfiguration {
        make(appName: webDomain.domain, token: nil)
    }

    private func make(appName: String?, token: ApplicationToken?) -> ShieldConfiguration {
        let snapshot = SnapshotStore.load()
        let appDay = snapshot.app(named: appName)
        let limitMinutes = token.map { ScreenTimeConfig.load().minutes(for: $0) } ?? Settings.defaultLimit
        let passes = Passes.remaining()
        let shownToday = Self.recordShown(appName: appName)

        let secondary: ShieldConfiguration.Label? = passes > 0
            ? ShieldConfiguration.Label(text: "5 more minutes · \(passes) \(passes == 1 ? "pass" : "passes") left", color: UIPalette.ink)
            : nil

        // Control week: plain, Screen Time-style shield.
        guard snapshot.nudgesOn else {
            return ShieldConfiguration(
                backgroundBlurStyle: .systemThinMaterialLight,
                backgroundColor: UIPalette.background.withAlphaComponent(0.92),
                icon: UIImage(systemName: "hourglass"),
                title: ShieldConfiguration.Label(text: CopyBank.plainShieldTitle, color: UIPalette.ink),
                subtitle: ShieldConfiguration.Label(text: CopyBank.plainShieldSubtitle(limitMinutes: limitMinutes), color: UIPalette.body),
                primaryButtonLabel: ShieldConfiguration.Label(text: "Close the app", color: UIPalette.card),
                primaryButtonBackgroundColor: UIPalette.ink,
                secondaryButtonLabel: secondary
            )
        }

        // Title: today's visit count for this app, when Shortcuts is tracking it.
        let title: String
        if let visits = appDay?.visits, visits > 0 {
            title = "Visit \(visits) today"
        } else {
            title = "Limit reached"
        }

        let line = CopyBank.line(
            voice: snapshot.voice, level: .shield, seed: (appDay?.visits ?? 0) + shownToday,
            context: .init(visit: appDay?.visits ?? 0, app: appName ?? "this app", elapsedSeconds: appDay?.seconds ?? 0)
        )
        let time: String
        if let seconds = appDay?.seconds, seconds > 0 {
            time = "\(Format.duration(seconds)) here today."
        } else {
            time = "Past your \(limitMinutes)-minute limit for today."
        }

        return ShieldConfiguration(
            backgroundBlurStyle: .systemThinMaterialLight,
            backgroundColor: UIPalette.background.withAlphaComponent(0.92),
            icon: UIImage(systemName: "face.smiling")?.withTintColor(UIPalette.accent, renderingMode: .alwaysOriginal),
            title: ShieldConfiguration.Label(text: title, color: UIPalette.accent),
            subtitle: ShieldConfiguration.Label(text: "\(line)\n\n\(time)", color: UIPalette.ink),
            primaryButtonLabel: ShieldConfiguration.Label(text: "Close the app", color: UIPalette.card),
            primaryButtonBackgroundColor: UIPalette.ink,
            secondaryButtonLabel: secondary
        )
    }

    /// Logs "shield shown" (at most once per 20 s, since iOS may ask for the
    /// configuration repeatedly) and returns how many times it was shown today,
    /// which rotates the copy.
    private static func recordShown(appName: String?, now: Date = Date()) -> Int {
        let defaults = AppGroup.defaults
        let lastKey = "shieldLastShown", countKey = "shieldShownCount", dayKey = "shieldShownDay"
        var count = defaults.integer(forKey: countKey)
        if let day = defaults.object(forKey: dayKey) as? Date, !Calendar.current.isDate(day, inSameDayAs: now) {
            count = 0
        }
        if let last = defaults.object(forKey: lastKey) as? Date, now.timeIntervalSince(last) < 20 {
            return count
        }
        count += 1
        defaults.set(now, forKey: lastKey)
        defaults.set(count, forKey: countKey)
        defaults.set(now, forKey: dayKey)
        EventLog.log(.shieldShown, app: appName, level: NudgeLevel.shield.rawValue, note: "shield #\(count) today")
        return count
    }
}
