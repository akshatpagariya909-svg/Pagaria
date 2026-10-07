import SwiftUI

/// Recap.dc.html: the weekly receipt.
struct WeekView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    @Binding var tab: AppTab
    @State private var rendered: UIImage?

    var body: some View {
        let receipt = WeekReceipt(stats: model.stats)
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Your week")
                        .font(Typo.display(30))
                        .tracking(-0.6)
                    Spacer()
                    Text(receipt.range).font(Typo.mono(12))
                }
                .foregroundStyle(Palette.paper)

                ReceiptCard(receipt: receipt)
                    .rotationEffect(.degrees(-1.2))
                    .padding(.vertical, 6)

                HStack(spacing: 10) {
                    if let rendered {
                        ShareLink(
                            item: Image(uiImage: rendered),
                            preview: SharePreview("My Unscroll receipt", image: Image(uiImage: rendered))
                        ) {
                            Text("Share receipt")
                        }
                        .buttonStyle(PrimaryButtonStyle(fill: Palette.paper, text: Palette.ink, height: 54))
                    } else {
                        Button("Share receipt") {}
                            .buttonStyle(PrimaryButtonStyle(fill: Palette.paper, text: Palette.ink, height: 54))
                            .disabled(true)
                    }
                    Button("Set next week") { tab = .limits }
                        .buttonStyle(SecondaryButtonStyle(text: Palette.paper, stroke: Palette.paper.opacity(0.5), height: 54))
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 120)
        }
        .scrollIndicators(.hidden)
        .screenBackground(Palette.moss)
        .task(id: receipt) { @MainActor in render(receipt) }
    }

    @MainActor
    private func render(_ receipt: WeekReceipt) {
        let card = ReceiptCard(receipt: receipt)
            .frame(width: 360)
            .padding(24)
            .background(Palette.moss)
            .environment(\.colorScheme, .light)
        let renderer = ImageRenderer(content: card)
        renderer.scale = displayScale
        rendered = renderer.uiImage
    }
}

/// Numbers for the receipt. Everything is computed from the event log.
struct WeekReceipt: Hashable {
    var number: Int
    var range: String
    var visits: Int
    var seconds: Int
    var longest: String
    var passesUsed: Int
    var passesAvailable: Int
    /// This week minus last week over the same number of elapsed days. Nil without last-week data.
    var deltaSeconds: Int?
    var weekComplete: Bool
    var walkAways: Int

    var metres: Double { Odometer.metres(seconds: seconds) }

    init(stats: Stats) {
        let now = stats.now
        let week = stats.weekInterval(containing: now)
        let cal = Calendar.current
        let this = stats.summary(week)

        number = cal.component(.weekOfYear, from: now)
        let fmt = Date.FormatStyle().day().month(.abbreviated)
        let lastDay = week.end.addingTimeInterval(-1)
        range = "\(week.start.formatted(fmt)) – \(lastDay.formatted(fmt))".uppercased()

        visits = this.visits
        seconds = this.seconds
        walkAways = this.walkAways
        passesUsed = this.passes
        passesAvailable = Settings.passesPerDay * 7

        if let l = this.longest {
            longest = "\(l.start.formatted(.dateTime.weekday(.abbreviated))) · \(Format.duration(l.seconds))"
        } else {
            longest = "–"
        }

        // Compare like with like: last week up to the same point in the week.
        let elapsed = now.timeIntervalSince(week.start)
        let lastStart = cal.date(byAdding: .day, value: -7, to: week.start) ?? week.start
        let lastSame = DateInterval(start: lastStart, duration: min(elapsed, 7 * 86_400))
        let hasLastWeekData = stats.events.contains { $0.type == .open && $0.ts >= lastStart && $0.ts < week.start }
        deltaSeconds = hasLastWeekData ? this.seconds - stats.summary(lastSame, includeLive: false).seconds : nil
        weekComplete = now >= week.end
    }
}

struct ReceiptCard: View {
    var receipt: WeekReceipt

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(spacing: 4) {
                Text("UNSCROLL")
                    .font(Typo.display(26))
                    .tracking(-0.5)
                Text("RECEIPT #\(receipt.number) · THANK YOU FOR YOUR ATTENTION")
                    .font(Typo.mono(11))
                    .foregroundStyle(Palette.muted)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.bottom, 10)
            .overlay(alignment: .bottom) { DashedRule() }

            row("Visits", "\(receipt.visits)")
            row("Time scrolled", Format.duration(receipt.seconds))
            row("Thumb distance*", Odometer.format(metres: receipt.metres))
            row("Longest spiral", receipt.longest)
            row("Passes used", "\(receipt.passesUsed) / \(receipt.passesAvailable)")

            VStack(spacing: 0) {
                DashedRule()
                HStack {
                    Text(receipt.weekComplete ? "vs last week" : "vs last week, same days")
                    Spacer()
                    Text(deltaText).foregroundStyle(deltaColor)
                }
                .font(Typo.mono(14, weight: .medium))
                .padding(.top, 10)
            }

            HStack(alignment: .firstTextBaseline) {
                Text("WALK-AWAYS").font(Typo.mono(14, weight: .medium))
                Spacer()
                Text("\(receipt.walkAways)")
                    .font(Typo.display(40))
                    .foregroundStyle(Palette.accent)
            }
            .padding(.vertical, 12)
            .overlay(alignment: .top) { Rectangle().fill(Palette.ink).frame(height: 1.5) }
            .overlay(alignment: .bottom) { Rectangle().fill(Palette.ink).frame(height: 1.5) }

            Text("Times you closed the app within a minute of a nudge. That's the number we care about.")
                .font(Typo.mono(12))
                .lineSpacing(4)
                .foregroundStyle(Palette.body)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
            Text("*estimated from time spent")
                .font(Typo.mono(10))
                .foregroundStyle(Palette.muted)
                .frame(maxWidth: .infinity)
        }
        .font(Typo.mono(14))
        .foregroundStyle(Palette.ink)
        .padding(EdgeInsets(top: 26, leading: 24, bottom: 30, trailing: 24))
        .background(
            Palette.card,
            in: UnevenRoundedRectangle(topLeadingRadius: 6, bottomLeadingRadius: 0,
                                       bottomTrailingRadius: 0, topTrailingRadius: 6)
        )
        .shadow(color: Color(hex: 0x14190A, opacity: 0.3), radius: 20, y: 20)
    }

    private func row(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
            Spacer()
            Text(value)
        }
    }

    private var deltaText: String {
        guard let delta = receipt.deltaSeconds else { return "no data yet" }
        if delta == 0 { return "same" }
        return (delta < 0 ? "−" : "+") + Format.duration(abs(delta))
    }

    private var deltaColor: Color {
        guard let delta = receipt.deltaSeconds else { return Palette.muted }
        return delta <= 0 ? Palette.moss : Palette.accent
    }
}
