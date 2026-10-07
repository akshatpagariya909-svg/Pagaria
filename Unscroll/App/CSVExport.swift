import Foundation

/// "Export test data": every logged event as CSV, for comparing week 1 (nudges off)
/// with week 2 (nudges on).
enum CSVExport {
    static let columns = [
        "timestamp", "date", "hour", "type", "app", "session", "visit",
        "seconds", "level", "nudges_on", "voice", "note",
    ]

    static func makeFile(events: [LogEvent] = EventLog.readAll()) throws -> URL {
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime]
        iso.timeZone = .current
        let day = DateFormatter()
        day.dateFormat = "yyyy-MM-dd"
        let cal = Calendar.current

        var rows = [columns.joined(separator: ",")]
        for e in events {
            let fields: [String] = [
                iso.string(from: e.ts),
                day.string(from: e.ts),
                "\(cal.component(.hour, from: e.ts))",
                e.type.rawValue,
                e.app ?? "",
                e.session?.uuidString ?? "",
                e.visit.map(String.init) ?? "",
                e.seconds.map(String.init) ?? "",
                e.level.map(String.init) ?? "",
                e.nudgesOn ? "1" : "0",
                e.voice,
                e.note ?? "",
            ]
            rows.append(fields.map(escape).joined(separator: ","))
        }

        let stamp = day.string(from: Date())
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("unscroll-events-\(stamp).csv")
        try rows.joined(separator: "\n").appending("\n").write(to: url, atomically: true, encoding: .utf8)
        return url
    }

    private static func escape(_ field: String) -> String {
        guard field.contains(where: { $0 == "," || $0 == "\"" || $0 == "\n" }) else { return field }
        return "\"" + field.replacingOccurrences(of: "\"", with: "\"\"") + "\""
    }
}
