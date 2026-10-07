import SwiftUI
import WidgetKit

// MARK: Small: "Visits today"

struct VisitsWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "VisitsToday", provider: SnapshotProvider()) { entry in
            VisitsWidgetView(snapshot: entry.snapshot)
                .containerBackground(Palette.card, for: .widget)
        }
        .configurationDisplayName("Visits today")
        .description("How many times you've opened your watched apps today.")
        .supportedFamilies([.systemSmall])
    }
}

struct VisitsWidgetView: View {
    var snapshot: DaySnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Visits today").monoCaps(color: Palette.muted)
            Spacer(minLength: 4)
            Text("\(snapshot.totalVisits)")
                .font(Typo.display(72))
                .tracking(-3.6)
                .foregroundStyle(Palette.accent)
                .lineLimit(1)
                .minimumScaleFactor(0.5)
                .contentTransition(.numericText())
            Spacer(minLength: 4)
            Text(WidgetCopy.visits(snapshot.totalVisits, voice: snapshot.voice))
                .font(Typo.text(13, weight: .semibold))
                .foregroundStyle(Palette.ink)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }
}

// MARK: Medium: "Thumb odometer"

struct OdometerWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "ThumbOdometer", provider: SnapshotProvider()) { entry in
            OdometerWidgetView(snapshot: entry.snapshot)
                .containerBackground(Palette.ink, for: .widget)
        }
        .configurationDisplayName("Thumb odometer")
        .description("Estimated scrolling distance today, against yesterday and your limit.")
        .supportedFamilies([.systemMedium])
    }
}

struct OdometerWidgetView: View {
    var snapshot: DaySnapshot

    /// Scale end, rounded up to a tidy 100 m.
    private var scaleMax: Double {
        let top = max(snapshot.metres, snapshot.yesterdayMetres, snapshot.limitMetres, 100) * 1.2
        return (top / 100).rounded(.up) * 100
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Thumb odometer").monoCaps(color: Palette.darkLabel)
                Spacer()
                Text("est.").font(Typo.mono(11)).foregroundStyle(Palette.darkLabel)
            }
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(Odometer.format(metres: snapshot.metres))
                    .font(Typo.display(48))
                    .tracking(-1.9)
                    .foregroundStyle(Palette.card)
                    .lineLimit(1)
                    .minimumScaleFactor(0.6)
                Text(Odometer.shortComparison(metres: snapshot.metres))
                    .font(Typo.text(14, weight: .semibold))
                    .foregroundStyle(Palette.peach)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            Spacer(minLength: 0)
            DistanceBar(
                today: snapshot.metres / scaleMax,
                yesterday: snapshot.yesterdayMetres / scaleMax,
                limit: snapshot.limitMetres / scaleMax,
                maxLabel: Odometer.format(metres: scaleMax)
            )
        }
    }
}

/// Bar with markers for yesterday and the limit; labels sit under their markers.
struct DistanceBar: View {
    var today: Double
    var yesterday: Double
    var limit: Double
    var maxLabel: String

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let yX = w * min(1, yesterday)
            let lX = w * min(1, limit)
            ZStack(alignment: .topLeading) {
                Capsule().fill(Palette.darkTrack).frame(height: 10)
                Capsule().fill(Palette.peach).frame(width: max(10, w * min(1, today)), height: 10)
                marker(at: yX)
                marker(at: lX)
                label("0", x: 0, anchor: .leading, w: w)
                label(maxLabel, x: w, anchor: .trailing, w: w)
                if yesterday > 0 {
                    label("yesterday", x: yX, anchor: .center, w: w)
                }
                label("your limit", x: lX, anchor: .center, w: w,
                      y: abs(yX - lX) < 64 && yesterday > 0 ? -16 : 18)
            }
        }
        .frame(height: 30)
    }

    private func marker(at x: CGFloat) -> some View {
        Rectangle().fill(Palette.card).frame(width: 2, height: 16).offset(x: x - 1, y: -3)
    }

    private func label(_ text: String, x: CGFloat, anchor: HorizontalAlignment, w: CGFloat, y: CGFloat = 18) -> some View {
        let estimated = CGFloat(text.count) * 6.2
        let left: CGFloat
        switch anchor {
        case .leading: left = x
        case .trailing: left = x - estimated
        default: left = min(max(0, x - estimated / 2), w - estimated)
        }
        return Text(text)
            .font(Typo.mono(10))
            .foregroundStyle(Palette.darkLabel)
            .fixedSize()
            .offset(x: left, y: y)
    }
}

// MARK: Lock screen

struct LimitCircularWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "LimitCircular", provider: SnapshotProvider()) { entry in
            LimitCircularView(snapshot: entry.snapshot)
                .containerBackground(for: .widget) { AccessoryWidgetBackground() }
        }
        .configurationDisplayName("% of limit")
        .description("Today's time as a share of your daily limits.")
        .supportedFamilies([.accessoryCircular])
    }
}

struct LimitCircularView: View {
    var snapshot: DaySnapshot

    var body: some View {
        let fraction = snapshot.limitFraction
        Gauge(value: min(1, fraction)) {
            Image(systemName: "hourglass")
        } currentValueLabel: {
            Text("\(Int((fraction * 100).rounded(.down)))%")
                .font(Typo.display(14))
        }
        .gaugeStyle(.accessoryCircularCapacity)
        .accessibilityLabel("\(Int((fraction * 100).rounded(.down))) percent of today's limit")
    }
}

struct VisitsRectangularWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "VisitsRectangular", provider: SnapshotProvider()) { entry in
            VisitsRectangularView(snapshot: entry.snapshot)
                .containerBackground(Color.clear, for: .widget)
        }
        .configurationDisplayName("Visits and time")
        .description("Visits today and time spent, at a glance.")
        .supportedFamilies([.accessoryRectangular])
    }
}

struct VisitsRectangularView: View {
    var snapshot: DaySnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("Visit \(snapshot.totalVisits) · \(Format.compactDuration(snapshot.totalSeconds))")
                .font(Typo.display(17))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text("\(snapshot.walkAways) walk-aways · \(Odometer.format(metres: snapshot.metres)) est.")
                .font(Typo.text(12))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
                .opacity(0.85)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
