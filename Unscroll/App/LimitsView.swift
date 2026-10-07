import FamilyControls
import SwiftUI

struct LimitsView: View {
    @Environment(AppModel.self) private var model
    @AppStorage(Settings.Key.defaultLimit, store: AppGroup.defaults) private var defaultLimit = Settings.defaultLimitMinutes
    @State private var apps: [String] = Settings.trackedApps
    @State private var limits: [String: Int] = Settings.appLimits
    @State private var newApp = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                VStack(alignment: .leading, spacing: 2) {
                    MonoLabel("Daily limits")
                    Text("Limits").font(Typo.display(36)).tracking(-1.1)
                }
                .foregroundStyle(Palette.ink)

                shortcutsLimits
                if FeatureFlags.screenTime {
                    ScreenTimeLimitsCard()
                } else {
                    ScreenTimeDisabledCard()
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 120)
        }
        .scrollIndicators(.hidden)
        .screenBackground()
        .onAppear {
            apps = Settings.trackedApps
            limits = Settings.appLimits
        }
    }

    private var shortcutsLimits: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Watched via Shortcuts")
                .font(Typo.text(18, weight: .bold))
            Text("These drive the Live Activity ring and the bars on Today. Names must match the app name in your automations.")
                .font(Typo.text(14))
                .foregroundStyle(Palette.body)

            ForEach(apps, id: \.self) { app in
                Stepper(value: binding(for: app), in: 5...240, step: 5) {
                    HStack {
                        Text(app).font(Typo.text(15, weight: .bold))
                        Spacer()
                        Text("\(limits[app] ?? defaultLimit) min").font(Typo.mono(13))
                    }
                }
                .contextMenu { Button("Stop watching \(app)", role: .destructive) { remove(app) } }
            }

            HStack(spacing: 10) {
                TextField("Add an app, e.g. YouTube", text: $newApp)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .submitLabel(.done)
                    .onSubmit(add)
                    .padding(.horizontal, 14)
                    .frame(height: 44)
                    .card(radius: 22, fill: Palette.background)
                Button("Add", action: add)
                    .font(Typo.text(15, weight: .bold))
                    .disabled(newApp.trimmingCharacters(in: .whitespaces).isEmpty)
            }

            Divider().overlay(Palette.border)

            Stepper(value: $defaultLimit, in: 5...240, step: 5) {
                HStack {
                    Text("Default for new apps").font(Typo.text(15))
                    Spacer()
                    Text("\(defaultLimit) min").font(Typo.mono(13))
                }
            }
            .onChange(of: defaultLimit) { _, _ in Tracker.refresh() }
        }
        .foregroundStyle(Palette.ink)
        .padding(18)
        .card(radius: 26)
    }

    private func binding(for app: String) -> Binding<Int> {
        Binding(
            get: { limits[app] ?? defaultLimit },
            set: { value in
                limits[app] = value
                Settings.appLimits = limits
                Tracker.refresh()
                model.reload()
            }
        )
    }

    private func add() {
        let name = newApp.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        Settings.track(name)
        apps = Settings.trackedApps
        newApp = ""
        Tracker.refresh()
        model.reload()
    }

    private func remove(_ app: String) {
        Settings.trackedApps = Settings.trackedApps.filter { $0 != app }
        limits[app] = nil
        Settings.appLimits = limits
        apps = Settings.trackedApps
        Tracker.refresh()
        model.reload()
    }
}

/// FamilyActivityPicker + per-app limits + monitoring (Screen Time layer).
struct ScreenTimeLimitsCard: View {
    @State private var config = ScreenTimeConfig.load()
    @State private var showPicker = false
    @State private var authorized = ScreenTimeManager.isAuthorized
    @State private var status: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("Screen Time shield").font(Typo.text(18, weight: .bold))
                Spacer()
                MonoLabel(authorized ? "on" : "off", color: authorized ? Palette.moss : Palette.muted, size: 11)
            }
            Text("Past the limit, the app is covered by a shield whose line changes every time you come back. 3 passes of 5 minutes a day.")
                .font(Typo.text(14))
                .foregroundStyle(Palette.body)

            if !authorized {
                Button("Allow Screen Time access") {
                    Task { authorized = await ScreenTimeManager.requestAuthorization() }
                }
                .buttonStyle(PrimaryButtonStyle(height: 48))
            } else {
                Button(config.limits.isEmpty ? "Choose apps" : "Change apps (\(config.limits.count))") {
                    showPicker = true
                }
                .buttonStyle(SecondaryButtonStyle())

                ForEach(config.limits.indices, id: \.self) { index in
                    Stepper(value: $config.limits[index].minutes, in: 5...240, step: 5) {
                        HStack {
                            Label(config.limits[index].token)
                                .labelStyle(.titleAndIcon)
                                .font(Typo.text(15, weight: .bold))
                            Spacer()
                            Text("\(config.limits[index].minutes) min").font(Typo.mono(13))
                        }
                    }
                }

                if !config.selection.categoryTokens.isEmpty {
                    Text("Categories are ignored: pick individual apps so each one gets its own limit.")
                        .font(Typo.text(13))
                        .foregroundStyle(Palette.accent)
                }

                Button("Save and start monitoring", action: save)
                    .buttonStyle(PrimaryButtonStyle(height: 48))
            }

            if let status {
                Text(status).font(Typo.mono(12)).foregroundStyle(Palette.muted)
            }
        }
        .foregroundStyle(Palette.ink)
        .padding(18)
        .card(radius: 26)
        .familyActivityPicker(isPresented: $showPicker, selection: $config.selection)
        .onChange(of: config.selection) { _, _ in config.syncLimits() }
    }

    private func save() {
        do {
            try ScreenTimeManager.apply(config)
            status = "Monitoring \(config.limits.count) app(s). Thresholds: 10 min, 20 min, limit."
        } catch {
            status = "Couldn't start monitoring: \(error.localizedDescription)"
        }
    }
}

struct ScreenTimeDisabledCard: View {
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "info.circle")
                .font(.system(size: 20))
            Text("Screen Time features are turned off in this build: the Family Controls entitlement couldn't be signed for your team. Visit counts, nudges, the Live Activity and widgets still work. Rebuild with project.yml once your account supports Family Controls.")
                .font(Typo.text(14))
                .lineSpacing(2)
        }
        .foregroundStyle(Palette.bodyDark)
        .padding(16)
        .background(Palette.info, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}
