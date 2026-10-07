import SwiftUI
import UserNotifications

struct SettingsView: View {
    @Environment(AppModel.self) private var model
    @AppStorage(Settings.Key.voice, store: AppGroup.defaults) private var voice: Voice = .witty
    @AppStorage(Settings.Key.nudgesOn, store: AppGroup.defaults) private var nudgesOn = true
    @State private var notificationStatus: UNAuthorizationStatus = .notDetermined
    @State private var showGuide = false
    @State private var export: ExportFile?
    @State private var confirmReset = false
    @State private var exportError: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    VStack(alignment: .leading, spacing: 2) {
                        MonoLabel("Unscroll")
                        Text("Settings").font(Typo.display(36)).tracking(-1.1)
                    }
                    .foregroundStyle(Palette.ink)

                    section("Voice") {
                        VoicePicker(voice: $voice)
                            .onChange(of: voice) { _, new in model.logSettingChange("voice=\(new.rawValue)") }
                    }

                    section("Experiment") {
                        Toggle(isOn: $nudgesOn) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Nudges").font(Typo.text(16, weight: .bold))
                                Text(nudgesOn
                                     ? "On: Live Activity, 10/20-minute nudges and witty shield copy."
                                     : "Off: counting only. The shield shows plain Screen Time-style text.")
                                    .font(Typo.text(13))
                                    .foregroundStyle(Palette.body)
                            }
                        }
                        .tint(Palette.accent)
                        .onChange(of: nudgesOn) { _, on in model.logSettingChange("nudges=\(on ? "on" : "off")") }
                        Text("Week 1: nudges off. Week 2: nudges on. Every event records which mode it happened in, so the CSV splits cleanly.")
                            .font(Typo.mono(11))
                            .foregroundStyle(Palette.muted)
                    }

                    section("Permissions") {
                        row("Notifications", value: notificationLabel) {
                            Task {
                                _ = await Nudges.requestPermission()
                                await refreshNotificationStatus()
                            }
                        }
                        row("Shortcuts automations", value: "Guide") { showGuide = true }
                        if FeatureFlags.screenTime {
                            row("Screen Time", value: ScreenTimeManager.isAuthorized ? "Allowed" : "Allow") {
                                Task { _ = await ScreenTimeManager.requestAuthorization() }
                            }
                        } else {
                            row("Screen Time", value: "Off in this build") {}
                                .disabled(true)
                        }
                    }

                    section("Test data") {
                        Text("\(model.events.count) events logged.")
                            .font(Typo.mono(12))
                            .foregroundStyle(Palette.muted)
                        Button("Export test data (CSV)") {
                            do { export = ExportFile(url: try CSVExport.makeFile(events: model.events)) } catch {
                                exportError = error.localizedDescription
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle(height: 48))
                        if let exportError {
                            Text(exportError).font(Typo.mono(11)).foregroundStyle(Palette.accent)
                        }
                        Button("Reset all data", role: .destructive) { confirmReset = true }
                            .buttonStyle(SecondaryButtonStyle(text: Palette.accent, stroke: Palette.accent.opacity(0.4)))
                    }

                    DebugPanel()
                }
                .padding(.horizontal, 20)
                .padding(.top, 12)
                .padding(.bottom, 120)
            }
            .scrollIndicators(.hidden)
            .screenBackground()
            .toolbar(.hidden, for: .navigationBar)
            .sheet(isPresented: $showGuide) {
                ScrollView { ShortcutsGuideView().padding(20) }
                    .screenBackground()
                    .presentationDragIndicator(.visible)
            }
            .sheet(item: $export) { file in
                ActivityView(items: [file.url])
            }
            .confirmationDialog("Delete every logged event and session?", isPresented: $confirmReset, titleVisibility: .visible) {
                Button("Delete all data", role: .destructive) {
                    Task { await model.resetAll() }
                }
            }
            .task { await refreshNotificationStatus() }
        }
    }

    private var notificationLabel: String {
        switch notificationStatus {
        case .authorized, .provisional, .ephemeral: return "Allowed"
        case .denied: return "Denied (Settings app)"
        default: return "Allow"
        }
    }

    private func refreshNotificationStatus() async {
        notificationStatus = await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
    }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            MonoLabel(title)
            content()
        }
        .foregroundStyle(Palette.ink)
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .card(radius: 26)
    }

    private func row(_ title: String, value: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Text(title).font(Typo.text(15, weight: .semibold)).foregroundStyle(Palette.ink)
                Spacer()
                Text(value).font(Typo.mono(13)).foregroundStyle(Palette.accent)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

/// Wraps the exported file so it can drive `.sheet(item:)`.
struct ExportFile: Identifiable {
    let url: URL
    var id: URL { url }
}

/// Simulate opens/closes without Shortcuts, and run the whole ladder in seconds.
struct DebugPanel: View {
    @Environment(AppModel.self) private var model
    @AppStorage(Settings.Key.fastLadder, store: AppGroup.defaults) private var fastLadder = false
    @State private var appName = "Instagram"
    @State private var lastLine: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            MonoLabel("Debug panel", color: Palette.accent)

            TextField("App name", text: $appName)
                .textInputAutocapitalization(.words)
                .autocorrectionDisabled()
                .padding(.horizontal, 14)
                .frame(height: 44)
                .card(radius: 22, fill: Palette.background)

            HStack(spacing: 10) {
                Button("Simulate open") {
                    Task {
                        let line = await model.simulateOpen(appName)
                        lastLine = "Banner: \u{201C}\(line)\u{201D}"
                    }
                }
                .buttonStyle(PrimaryButtonStyle(height: 44))
                Button("Simulate close") {
                    Task {
                        let before = model.stats.today.walkAways
                        await model.simulateClose(appName)
                        lastLine = model.stats.today.walkAways > before
                            ? "Closed within a minute of a nudge: walk-away logged."
                            : "Closed. No walk-away (no nudge or shield in the last 60 s)."
                    }
                }
                .buttonStyle(SecondaryButtonStyle(height: 44))
            }

            if let lastLine {
                Text(lastLine)
                    .font(Typo.text(14))
                    .foregroundStyle(Palette.body)
            }

            Toggle(isOn: $fastLadder) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Fast ladder").font(Typo.text(15, weight: .semibold))
                    Text("Nudges at +10 s / +20 s instead of minutes, limit = 1 min. Copy shows the real elapsed time.")
                        .font(Typo.text(12))
                        .foregroundStyle(Palette.body)
                }
            }
            .tint(Palette.accent)
            .onChange(of: fastLadder) { _, on in model.logSettingChange("fastLadder=\(on ? "on" : "off")") }

            if FeatureFlags.screenTime {
                HStack(spacing: 10) {
                    Button("Shield now") { ScreenTimeManager.shieldNow() }
                        .buttonStyle(SecondaryButtonStyle(height: 44))
                    Button("Clear shields") { ScreenTimeManager.clearShields() }
                        .buttonStyle(SecondaryButtonStyle(height: 44))
                }
                Text("Passes left today: \(Passes.remaining())")
                    .font(Typo.mono(12))
                    .foregroundStyle(Palette.muted)
            }

            if !model.openSessions.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(model.openSessions, id: \.id) { session in
                        HStack {
                            Text("\(session.app) · visit \(session.visit)")
                            Spacer()
                            Text(timerInterval: session.start...session.start.addingTimeInterval(12 * 3600), countsDown: false)
                                .monospacedDigit()
                        }
                        .font(Typo.mono(12))
                    }
                }
                .foregroundStyle(Palette.body)
            }

            Text("Last events")
                .font(Typo.text(13, weight: .semibold))
            ForEach(Array(model.events.suffix(6).reversed())) { event in
                Text("\(event.ts.formatted(date: .omitted, time: .standard))  \(event.type.rawValue)  \(event.app ?? "")\(event.level.map { " L\($0)" } ?? "")\(event.seconds.map { " \($0)s" } ?? "")")
                    .font(Typo.mono(11))
                    .foregroundStyle(Palette.muted)
                    .lineLimit(1)
            }
        }
        .foregroundStyle(Palette.ink)
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .card(radius: 26, border: Palette.accent.opacity(0.4))
    }
}
