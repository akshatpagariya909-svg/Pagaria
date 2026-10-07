import SwiftUI

enum AppTab: String, CaseIterable, Identifiable {
    case today, week, limits, settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .today: return "Today"
        case .week: return "Week"
        case .limits: return "Limits"
        case .settings: return "Settings"
        }
    }

    var icon: String {
        switch self {
        case .today: return "clock"
        case .week: return "scroll"
        case .limits: return "chart.bar"
        case .settings: return "slider.horizontal.3"
        }
    }
}

struct RootView: View {
    @AppStorage(Settings.Key.onboarded, store: AppGroup.defaults) private var onboarded = false
    @State private var tab: AppTab = .today

    var body: some View {
        if onboarded {
            ZStack(alignment: .bottom) {
                Group {
                    switch tab {
                    case .today: TodayView(tab: $tab)
                    case .week: WeekView(tab: $tab)
                    case .limits: LimitsView()
                    case .settings: SettingsView()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)

                FloatingTabBar(selection: $tab)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 4)
            }
        } else {
            OnboardingView {
                onboarded = true
            }
        }
    }
}

/// Floating glass tab bar (Home.dc.html <nav>).
struct FloatingTabBar: View {
    @Binding var selection: AppTab

    var body: some View {
        HStack(spacing: 4) {
            ForEach(AppTab.allCases) { tab in
                let selected = tab == selection
                Button {
                    selection = tab
                } label: {
                    VStack(spacing: 2) {
                        Image(systemName: tab.icon)
                            .font(.system(size: 18, weight: .medium))
                        Text(tab.title)
                            .font(Typo.text(11, weight: .semibold))
                    }
                    .foregroundStyle(selected ? Palette.card : Palette.ink)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background {
                        if selected {
                            Capsule().fill(Palette.ink.opacity(0.9))
                        }
                    }
                    .contentShape(Capsule())
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(selected ? .isSelected : [])
            }
        }
        .padding(6)
        .frame(height: 66)
        .floatingGlass(Capsule(), interactive: false) {
            // Pre-iOS 26: frosted cream, as in the mockup.
            ZStack {
                Capsule().fill(.ultraThinMaterial)
                Capsule().fill(Color(hex: 0xFBF6EE, opacity: 0.62))
                Capsule().strokeBorder(Color.white.opacity(0.85), lineWidth: 1)
            }
        }
        .shadow(color: Color(hex: 0x3C230F, opacity: 0.16), radius: 17, y: 14)
        .animation(.snappy(duration: 0.25), value: selection)
    }
}
