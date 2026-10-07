import ActivityKit
import SwiftUI
import WidgetKit

/// Dynamic Island + lock screen session pill (Widgets.dc.html, NudgeLadder.dc.html).
/// Timers and the limit ring are driven by `timerInterval`, so they tick with no updates.
struct SessionLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: SessionAttributes.self) { context in
            SessionLockScreenView(app: context.attributes.appName, state: context.state)
                .activityBackgroundTint(Color(hex: 0xFBF6EE, opacity: 0.85))
                .activitySystemActionForegroundColor(Palette.ink)
        } dynamicIsland: { context in
            let state = context.state
            return DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    VStack(spacing: 4) {
                        LimitRing(state: state)
                            .frame(width: 40, height: 40)
                        Text("visit \(state.visit)")
                            .font(Typo.mono(11))
                            .foregroundStyle(Color(hex: 0xF6ECDF))
                    }
                    .padding(.leading, 4)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    VStack(alignment: .trailing, spacing: 2) {
                        SessionTimer(state: state)
                            .font(Typo.display(28, weight: .bold))
                            .foregroundStyle(Color(hex: 0xFBF2E6))
                        Text("limit \(state.limitMinutes) min")
                            .font(Typo.mono(11))
                            .foregroundStyle(Palette.darkLabel)
                    }
                    .padding(.trailing, 4)
                }
                DynamicIslandExpandedRegion(.center) {
                    Text(context.attributes.appName)
                        .font(Typo.mono(12))
                        .foregroundStyle(Palette.darkLabel)
                        .lineLimit(1)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    Text(state.line)
                        .font(Typo.text(15, weight: .semibold))
                        .foregroundStyle(Color(hex: 0xFBF2E6))
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 4)
                        .padding(.top, 4)
                }
            } compactLeading: {
                HStack(spacing: 6) {
                    Circle().fill(Palette.accent).frame(width: 12, height: 12)
                    Text("visit \(state.visit)")
                        .font(Typo.mono(13))
                        .foregroundStyle(Color(hex: 0xF6ECDF))
                }
            } compactTrailing: {
                SessionTimer(state: state)
                    .font(Typo.mono(13))
                    .foregroundStyle(Color(hex: 0xF6ECDF))
                    .frame(maxWidth: 58)
            } minimal: {
                LimitRing(state: state)
                    .padding(2)
            }
            .keylineTint(Palette.accent)
        }
    }
}

/// Counts up from session start; never needs an update.
struct SessionTimer: View {
    var state: SessionAttributes.ContentState

    var body: some View {
        Text(timerInterval: state.timerRange, countsDown: false)
            .monospacedDigit()
            .multilineTextAlignment(.trailing)
    }
}

/// Fills toward today's per-app limit (time used before this session included).
struct LimitRing: View {
    var state: SessionAttributes.ContentState

    var body: some View {
        ProgressView(timerInterval: state.limitRange, countsDown: false) {
            EmptyView()
        } currentValueLabel: {
            EmptyView()
        }
        .progressViewStyle(.circular)
        .tint(Palette.accent)
    }
}

/// Lock screen banner: "In Instagram · visit 25 / Still fun? Honest answers only."
struct SessionLockScreenView: View {
    var app: String
    var state: SessionAttributes.ContentState

    private var question: String {
        switch SnapshotStore.load().voice {
        case .gentle: return "Still enjoying it? No pressure."
        case .witty: return "Still fun? Honest answers only."
        case .blunt: return "Still worth it? Be honest."
        }
    }

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: "face.smiling")
                .font(.system(size: 22, weight: .semibold))
                .foregroundStyle(Color(hex: 0xFFF8F0))
                .frame(width: 44, height: 44)
                .background(Palette.accent, in: RoundedRectangle(cornerRadius: 14, style: .continuous))

            VStack(alignment: .leading, spacing: 2) {
                // "Minute X": the ticking timer on the right is the live minute count,
                // since Live Activity text can't change without an update.
                Text("In \(app) · visit \(state.visit)")
                    .font(Typo.text(15, weight: .bold))
                    .lineLimit(1)
                Text(question)
                    .font(Typo.text(13))
                    .foregroundStyle(Palette.body)
                    .lineLimit(1)
                LimitBarTimer(state: state)
                    .padding(.top, 4)
            }

            Spacer(minLength: 4)

            VStack(alignment: .trailing, spacing: 0) {
                MinuteLabel()
                SessionTimer(state: state)
                    .font(Typo.mono(17, weight: .medium))
                    .frame(maxWidth: 76, alignment: .trailing)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .floatingGlass(RoundedRectangle(cornerRadius: 14, style: .continuous), interactive: false) {
                RoundedRectangle(cornerRadius: 14, style: .continuous).fill(Palette.card.opacity(0.7))
            }
        }
        .foregroundStyle(Palette.ink)
        .padding(EdgeInsets(top: 16, leading: 18, bottom: 16, trailing: 18))
    }
}

private struct MinuteLabel: View {
    var body: some View {
        Text("minute")
            .font(Typo.mono(10))
            .foregroundStyle(Palette.muted)
    }
}

/// Thin linear version of the limit ring for the lock screen.
struct LimitBarTimer: View {
    var state: SessionAttributes.ContentState

    var body: some View {
        ProgressView(timerInterval: state.limitRange, countsDown: false) {
            EmptyView()
        } currentValueLabel: {
            EmptyView()
        }
        .progressViewStyle(.linear)
        .tint(Palette.accent)
        .frame(maxWidth: 160)
    }
}
