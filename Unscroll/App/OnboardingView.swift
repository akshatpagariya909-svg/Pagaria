import SwiftUI

/// Onboarding.dc.html (step 2 is the approved voice picker).
struct OnboardingView: View {
    var onFinish: () -> Void

    @AppStorage(Settings.Key.voice, store: AppGroup.defaults) private var voice: Voice = .witty
    @State private var step = 1
    @State private var notificationsAllowed = false
    @State private var screenTimeAllowed = ScreenTimeManager.isAuthorized
    private let steps = 4

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack(spacing: 6) {
                ForEach(1...steps, id: \.self) { i in
                    Capsule()
                        .fill(i <= step ? Palette.ink : Palette.border)
                        .frame(height: 4)
                }
            }
            .animation(.easeOut, value: step)

            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    switch step {
                    case 1: intro
                    case 2: voiceStep
                    case 3: ShortcutsGuideView(stepLabel: "Step 3 of 4")
                    default: permissions
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .scrollIndicators(.hidden)

            HStack(spacing: 10) {
                if step > 1 {
                    Button("Back") { step -= 1 }
                        .buttonStyle(SecondaryButtonStyle(height: 56))
                        .frame(width: 110)
                }
                Button(step == steps ? "Start" : "Continue") {
                    if step == steps { onFinish() } else { step += 1 }
                }
                .buttonStyle(PrimaryButtonStyle())
            }
        }
        .foregroundStyle(Palette.ink)
        .padding(.horizontal, 20)
        .padding(.top, 20)
        .padding(.bottom, 12)
        .screenBackground()
    }

    private func heading(_ label: String, _ title: String, _ body: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel(label)
            Text(title)
                .font(Typo.display(38))
                .tracking(-1.1)
                .fixedSize(horizontal: false, vertical: true)
            Text(body)
                .font(Typo.text(16))
                .lineSpacing(3)
                .foregroundStyle(Palette.body)
        }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: 22) {
            heading("Step 1 of 4", "A friend who notices.",
                    "Screen Time nudges once. Unscroll keeps noticing, quietly, and gets a little more honest the longer you stay. No sound, no video, no guilt trips.")
            VStack(spacing: 12) {
                featureRow("number", "Measure", "Every open of a watched app is a visit. Time becomes a thumb odometer.")
                featureRow("bubble.left", "Nudge", "A Dynamic Island timer, then nudges at 10 and 20 minutes, then a shield.")
                featureRow("receipt", "Reflect", "Widgets and a weekly receipt that count your walk-aways.")
            }
            infoNote("iOS doesn't let apps see inside Instagram or YouTube, so distance is an estimate from time spent. Every other number is exact.")
        }
    }

    private var voiceStep: some View {
        VStack(alignment: .leading, spacing: 22) {
            heading("Step 2 of 4", "How should I talk to you?",
                    "This is what you'll see at visit 25. Pick the one you won't mute.")
            VoicePicker(voice: $voice)
            infoNote("I get a little more honest the longer you stay. You can switch voices anytime.")
        }
    }

    private var permissions: some View {
        VStack(alignment: .leading, spacing: 22) {
            heading("Step 4 of 4", "Last bit: permissions.",
                    "Nudges are silent notifications. The session timer is a Live Activity. Screen Time is optional and powers the shield.")
            VStack(spacing: 12) {
                permissionRow("Notifications", detail: "Silent nudges at 10 and 20 minutes.",
                              done: notificationsAllowed) {
                    Task { notificationsAllowed = await Nudges.requestPermission() }
                }
                permissionRow("Live Activities", detail: "On by default. Check Settings › Unscroll if the timer doesn't show.",
                              done: true) {}
                if FeatureFlags.screenTime {
                    permissionRow("Screen Time (optional)", detail: "Lets the shield cover apps past your limit.",
                                  done: screenTimeAllowed) {
                        Task { screenTimeAllowed = await ScreenTimeManager.requestAuthorization() }
                    }
                } else {
                    infoNote("Screen Time is off in this build, so there's no shield. Everything else works.")
                }
            }
        }
    }

    private func featureRow(_ icon: String, _ title: String, _ text: String) -> some View {
        HStack(alignment: .top, spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Palette.accent)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(Typo.text(18, weight: .bold))
                Text(text).font(Typo.text(15)).foregroundStyle(Palette.body)
            }
            Spacer(minLength: 0)
        }
        .padding(EdgeInsets(top: 18, leading: 20, bottom: 18, trailing: 20))
        .card(radius: 26)
    }

    private func permissionRow(_ title: String, detail: String, done: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 14) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(Typo.text(18, weight: .bold))
                    Text(detail).font(Typo.text(14)).foregroundStyle(Palette.body)
                }
                Spacer()
                Image(systemName: done ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 24))
                    .foregroundStyle(done ? Palette.moss : Palette.border)
            }
            .padding(EdgeInsets(top: 18, leading: 20, bottom: 18, trailing: 20))
            .card(radius: 26)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(done)
    }
}

/// Grey info note with the circle-i icon.
func infoNote(_ text: String) -> some View {
    HStack(alignment: .top, spacing: 12) {
        Image(systemName: "info.circle")
            .font(.system(size: 20))
            .foregroundStyle(Palette.ink)
        Text(text)
            .font(Typo.text(14))
            .lineSpacing(2)
            .foregroundStyle(Palette.bodyDark)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
    .padding(EdgeInsets(top: 14, leading: 16, bottom: 14, trailing: 16))
    .background(Palette.info, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
}

/// Three voice cards; the selected one gets the accent border + check.
struct VoicePicker: View {
    @Binding var voice: Voice

    var body: some View {
        VStack(spacing: 12) {
            ForEach(Voice.allCases) { option in
                let selected = option == voice
                Button {
                    voice = option
                } label: {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(option.title).font(Typo.text(18, weight: .bold))
                            Spacer()
                            if selected {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 12, weight: .heavy))
                                    .foregroundStyle(Color(hex: 0xFFF8F0))
                                    .frame(width: 24, height: 24)
                                    .background(Palette.accent, in: Circle())
                            }
                        }
                        Text(option.sample)
                            .font(Typo.text(15))
                            .lineSpacing(2)
                            .foregroundStyle(Palette.body)
                            .multilineTextAlignment(.leading)
                    }
                    .foregroundStyle(Palette.ink)
                    .padding(EdgeInsets(top: 18, leading: 20, bottom: 18, trailing: 20))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(selected ? Palette.selected : Palette.card,
                                 in: RoundedRectangle(cornerRadius: 26, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 26, style: .continuous)
                            .strokeBorder(selected ? Palette.accent : Palette.border, lineWidth: selected ? 2 : 1)
                    )
                    .shadow(color: selected ? Palette.accent.opacity(0.14) : .clear, radius: 12, y: 10)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(selected ? .isSelected : [])
            }
        }
        .animation(.easeOut(duration: 0.2), value: voice)
    }
}
