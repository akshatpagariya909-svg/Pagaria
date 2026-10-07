import SwiftUI

/// Home.dc.html
struct TodayView: View {
    @Environment(AppModel.self) private var model
    @Binding var tab: AppTab
    @AppStorage(Settings.Key.voice, store: AppGroup.defaults) private var voice: Voice = .witty

    private let refresh = Timer.publish(every: 30, on: .main, in: .common).autoconnect()

    var body: some View {
        let today = model.stats.today
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                header
                OdometerCard(seconds: today.seconds)
                tiles(today)
                appBars(today)
                voiceLine
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 120)
        }
        .scrollIndicators(.hidden)
        .screenBackground()
        .onReceive(refresh) { _ in model.reload() }
        .refreshable { model.reload() }
    }

    private var header: some View {
        HStack(alignment: .bottom) {
            VStack(alignment: .leading, spacing: 2) {
                MonoLabel(Date().formatted(.dateTime.weekday(.wide)))
                Text("Today")
                    .font(Typo.display(36))
                    .tracking(-1.1)
                    .foregroundStyle(Palette.ink)
            }
            Spacer()
            CircleIconButton(systemName: "slider.horizontal.3", label: "Settings") {
                tab = .settings
            }
        }
    }

    private func tiles(_ today: UsageSummary) -> some View {
        HStack(spacing: 10) {
            StatTile(value: "\(today.visits)", label: today.visits == 1 ? "visit" : "visits", color: Palette.accent)
            if today.seconds >= 3600 {
                StatTile(value: Format.clock(today.seconds), label: "hours here", color: Palette.ink)
            } else {
                StatTile(value: "\(today.seconds / 60)", label: "minutes here", color: Palette.ink)
            }
            StatTile(value: "\(today.walkAways)", label: today.walkAways == 1 ? "walk-away" : "walk-aways", color: Palette.moss)
        }
    }

    @ViewBuilder
    private func appBars(_ today: UsageSummary) -> some View {
        let names = Array(Set(Settings.trackedApps).union(today.apps.keys)).sorted {
            (today.apps[$0]?.seconds ?? 0, $1) > (today.apps[$1]?.seconds ?? 0, $0)
        }
        VStack(alignment: .leading, spacing: 14) {
            if names.isEmpty {
                Text("No watched apps yet. Set up the Shortcuts automations in Settings, or simulate a visit from the debug panel.")
                    .font(Typo.text(15))
                    .foregroundStyle(Palette.body)
            }
            ForEach(names, id: \.self) { name in
                let minutes = (today.apps[name]?.seconds ?? 0) / 60
                let limit = Settings.limitMinutes(for: name)
                let fraction = Double(minutes) / Double(max(limit, 1))
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(name).font(Typo.text(15, weight: .bold))
                        Spacer()
                        Text("\(minutes) / \(limit) min").font(Typo.mono(13))
                    }
                    .foregroundStyle(Palette.ink)
                    LimitBar(fraction: fraction, color: Self.barColor(fraction))
                }
                .accessibilityElement(children: .combine)
            }
        }
        .padding(.vertical, 16)
        .padding(.horizontal, 18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .card(radius: 26)
    }

    static func barColor(_ fraction: Double) -> Color {
        if fraction >= 1 { return Palette.accent }
        if fraction >= 0.6 { return Palette.amber }
        return Palette.moss
    }

    private var voiceLine: some View {
        HStack(alignment: .top, spacing: 12) {
            VoiceAvatar()
            Text(insight)
                .font(Typo.text(15))
                .lineSpacing(3)
                .foregroundStyle(Palette.bodyDark)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 4)
        .padding(.top, 4)
    }

    /// Only says what the data supports.
    private var insight: String {
        guard let hour = model.stats.riskiestHour() else {
            return "I need a few days of visits before I can spot your patterns. Keep the automations on."
        }
        var components = DateComponents()
        components.hour = hour
        let date = Calendar.current.date(from: components) ?? Date()
        let label = date.formatted(.dateTime.hour(.defaultDigits(amPM: .abbreviated))).lowercased()
        switch voice {
        case .gentle: return "Your riskiest hour lately is \(label). Maybe plan something cosy for then."
        case .witty: return "Your riskiest hour lately is \(label). Noted. Maybe keep a book within reach."
        case .blunt: return "Your riskiest hour lately is \(label). Plan around it."
        }
    }
}

struct StatTile: View {
    var value: String
    var label: String
    var color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(Typo.display(30))
                .tracking(-0.9)
                .foregroundStyle(color)
                .lineLimit(1)
                .minimumScaleFactor(0.6)
            Text(label)
                .font(Typo.text(13))
                .foregroundStyle(Palette.secondary)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .card(radius: 22)
        .accessibilityElement(children: .combine)
    }
}

/// Dark "Thumb odometer" hero card.
struct OdometerCard: View {
    var seconds: Int

    private var metres: Double { Odometer.metres(seconds: seconds) }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline) {
                MonoLabel("Thumb odometer", color: Palette.darkLabel)
                Spacer()
                Text("estimate").font(Typo.mono(11)).foregroundStyle(Palette.darkLabel)
            }
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text("\(Int(metres.rounded(.down)))")
                    .font(Typo.display(76))
                    .tracking(-3.8)
                    .foregroundStyle(Palette.card)
                    .contentTransition(.numericText())
                Text("metres")
                    .font(Typo.display(24, weight: .bold))
                    .foregroundStyle(Palette.peach)
            }
            Text(Odometer.comparison(metres: metres))
                .font(Typo.text(16))
                .lineSpacing(3)
                .foregroundStyle(Palette.darkBody)
            LandmarkBars(metres: metres)
        }
        .padding(22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Palette.ink, in: RoundedRectangle(cornerRadius: 30, style: .continuous))
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Thumb odometer, estimate: \(Int(metres)) metres. \(Odometer.comparison(metres: metres))")
    }
}

/// One bar per landmark height; the last bar is partial.
struct LandmarkBars: View {
    var metres: Double
    var maxBars = 12

    var body: some View {
        let mark = Odometer.landmark(for: metres)
        let ratio = min(Double(maxBars), metres / mark.metres)
        let full = Int(ratio)
        let partial = ratio - Double(full)
        let heights = Array(repeating: 1.0, count: full) + (partial > 0.02 ? [partial] : [])
        HStack(alignment: .bottom, spacing: 6) {
            ForEach(Array(heights.enumerated()), id: \.offset) { _, h in
                UnevenRoundedRectangle(topLeadingRadius: 4, bottomLeadingRadius: 1,
                                       bottomTrailingRadius: 1, topTrailingRadius: 4)
                    .fill(Palette.peach)
                    .frame(width: 14, height: max(3, 46 * h))
            }
            Spacer(minLength: 8)
            Text("1 bar = \(Self.metresLabel(mark.metres))")
                .font(Typo.mono(11))
                .foregroundStyle(Palette.darkLabel)
        }
        .frame(height: 46, alignment: .bottom)
    }

    static func metresLabel(_ m: Double) -> String {
        m == m.rounded() ? "\(Int(m)) m" : String(format: "%.1f m", m)
    }
}
