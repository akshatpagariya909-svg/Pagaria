import Foundation
import Observation

@Observable
final class AppModel {
    private(set) var stats = Stats(events: [], open: [:])

    init() {
        reload()
    }

    var events: [LogEvent] { stats.events }
    var openSessions: [OpenSession] { stats.open.values.sorted { $0.start < $1.start } }

    func reload() {
        stats = Stats.load()
        SnapshotStore.save(stats.snapshot())
    }

    /// Debug panel + Settings go through the same code path as the Shortcuts intents.
    func simulateOpen(_ app: String) async -> String {
        let line = await Tracker.appOpened(app)
        reload()
        return line
    }

    func simulateClose(_ app: String) async {
        await Tracker.appClosed(app)
        reload()
    }

    func resetAll() async {
        await Tracker.resetAllData()
        reload()
    }

    /// Records experiment switches so week 1 vs week 2 can be split in the CSV.
    func logSettingChange(_ note: String) {
        EventLog.log(.setting, note: note)
        Tracker.refresh()
        reload()
    }
}
