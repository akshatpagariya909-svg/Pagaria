import Foundation

/// Append-only JSON-lines log of every validation event, in the App Group.
/// Extensions append to it; only the app reads the whole thing.
enum EventLog {
    static let url = AppGroup.file("events.jsonl")

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    /// Builds an event stamped with the current experiment settings.
    static func make(
        _ type: EventType, app: String? = nil, session: UUID? = nil, visit: Int? = nil,
        seconds: Int? = nil, level: Int? = nil, note: String? = nil, at date: Date = Date()
    ) -> LogEvent {
        LogEvent(
            ts: date, type: type, app: app, session: session, visit: visit, seconds: seconds,
            level: level, nudgesOn: Settings.nudgesOn, voice: Settings.voice.rawValue, note: note
        )
    }

    static func append(_ event: LogEvent) {
        guard var line = try? encoder.encode(event) else { return }
        line.append(0x0A)
        coordinate(writing: true) { url in
            if let handle = try? FileHandle(forWritingTo: url) {
                defer { try? handle.close() }
                _ = try? handle.seekToEnd()
                try? handle.write(contentsOf: line)
            } else {
                try? line.write(to: url, options: .atomic)
            }
        }
    }

    static func log(
        _ type: EventType, app: String? = nil, session: UUID? = nil, visit: Int? = nil,
        seconds: Int? = nil, level: Int? = nil, note: String? = nil, at date: Date = Date()
    ) {
        append(make(type, app: app, session: session, visit: visit, seconds: seconds,
                    level: level, note: note, at: date))
    }

    static func readAll() -> [LogEvent] {
        var data = Data()
        coordinate(writing: false) { url in
            data = (try? Data(contentsOf: url)) ?? Data()
        }
        guard !data.isEmpty else { return [] }
        return data.split(separator: 0x0A).compactMap { try? decoder.decode(LogEvent.self, from: Data($0)) }
            .sorted { $0.ts < $1.ts }
    }

    static func reset() {
        coordinate(writing: true) { url in
            try? FileManager.default.removeItem(at: url)
        }
    }

    /// Several processes (app, monitor, shield) touch the same file.
    private static func coordinate(writing: Bool, _ body: (URL) -> Void) {
        let coordinator = NSFileCoordinator()
        var error: NSError?
        if writing {
            coordinator.coordinate(writingAt: url, options: [], error: &error, byAccessor: body)
        } else {
            coordinator.coordinate(readingItemAt: url, options: [], error: &error, byAccessor: body)
        }
    }
}
