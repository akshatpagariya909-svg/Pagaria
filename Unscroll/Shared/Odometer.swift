import Foundation

/// "Thumb odometer": an *estimate* of how far the thumb travelled, from time spent.
/// iOS can't see scrolls inside other apps, so this is time × a constant, and the
/// UI always labels it as an estimate.
enum Odometer {
    /// Estimated metres of feed scrolled per minute of use.
    static let metresPerMinute: Double = 3.8

    static func metres(seconds: Int) -> Double {
        Double(seconds) / 60 * metresPerMinute
    }

    struct Landmark: Hashable {
        let name: String      // "Qutub Minar"
        let plural: String    // "Qutub Minars"
        let metres: Double
        let stackVerb: String // "stacked" / "end to end"
    }

    static let qutubMinar = Landmark(name: "Qutub Minar", plural: "Qutub Minars", metres: 72.5, stackVerb: "stacked")
    static let footballField = Landmark(name: "football field", plural: "football fields", metres: 105, stackVerb: "end to end")
    static let eiffelTower = Landmark(name: "Eiffel Tower", plural: "Eiffel Towers", metres: 330, stackVerb: "stacked")

    /// Picks the landmark that keeps the comparison in a readable 0–10× range.
    static func landmark(for metres: Double) -> Landmark {
        if metres <= qutubMinar.metres * 10 { return qutubMinar }
        if metres <= footballField.metres * 10 { return footballField }
        return eiffelTower
    }

    /// Rounds *down* to the nearest half, so we never overstate.
    static func halves(_ value: Double) -> String {
        let h = (value * 2).rounded(.down) / 2
        let whole = Int(h)
        let hasHalf = h - Double(whole) >= 0.5
        if whole == 0 { return hasHalf ? "½" : "0" }
        return "\(whole)" + (hasHalf ? "½" : "")
    }

    /// "That's Qutub Minar, stacked 5½ times."
    static func comparison(metres: Double) -> String {
        guard metres >= 1 else { return "Nothing yet. Your thumb is well rested." }
        let mark = landmark(for: metres)
        let ratio = metres / mark.metres
        if ratio < 1 {
            let percent = Int((ratio * 100).rounded(.down))
            return "That's \(percent)% of a \(mark.name)."
        }
        let count = halves(ratio)
        if count == "1" { return "That's about one \(mark.name)." }
        if mark == footballField { return "That's \(count) football fields, end to end." }
        let article = mark == eiffelTower ? "the " : ""
        return "That's \(article)\(mark.name), \(mark.stackVerb) \(count) times."
    }

    /// Short form for widgets: "5½ Qutub Minars".
    static func shortComparison(metres: Double) -> String {
        let mark = landmark(for: metres)
        let ratio = metres / mark.metres
        if ratio < 1 { return "\(Int((ratio * 100).rounded(.down)))% of a \(mark.name)" }
        let count = halves(ratio)
        return count == "1" ? "1 \(mark.name)" : "\(count) \(mark.plural)"
    }

    /// For copy lines: "about one Qutub Minar".
    static func phrase(metres: Double) -> String {
        let mark = landmark(for: metres)
        let ratio = metres / mark.metres
        if ratio < 1 { return "\(Int((ratio * 100).rounded(.down)))% of a \(mark.name)" }
        let count = halves(ratio)
        return count == "1" ? "about one \(mark.name)" : "about \(count) \(mark.plural)"
    }

    /// "412 m" / "2.9 km"
    static func format(metres: Double) -> String {
        if metres >= 1000 {
            return String(format: "%.1f km", metres / 1000)
        }
        return "\(Int(metres.rounded(.down))) m"
    }
}

enum Format {
    /// "1 h 48 m", "38 m", "0 m"
    static func duration(_ seconds: Int) -> String {
        let minutes = max(0, seconds) / 60
        let h = minutes / 60
        let m = minutes % 60
        return h > 0 ? "\(h) h " + String(format: "%02d", m) + " m" : "\(m) m"
    }

    /// "1h48m" for the lock screen.
    static func compactDuration(_ seconds: Int) -> String {
        let minutes = seconds / 60
        let h = minutes / 60
        let m = minutes % 60
        return h > 0 ? "\(h)h\(String(format: "%02d", m))m" : "\(m)m"
    }

    /// "1:48" for the Today tile.
    static func clock(_ seconds: Int) -> String {
        let minutes = seconds / 60
        return "\(minutes / 60):" + String(format: "%02d", minutes % 60)
    }

    /// Human elapsed time for nudge copy, e.g. "10 minutes" or "20 seconds" (fast debug ladder).
    static func elapsed(seconds: Int) -> String {
        if seconds < 60 { return seconds == 1 ? "1 second" : "\(seconds) seconds" }
        let minutes = seconds / 60
        return minutes == 1 ? "1 minute" : "\(minutes) minutes"
    }
}
