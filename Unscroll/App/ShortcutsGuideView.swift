import SwiftUI
import UIKit

/// Walks through the two personal automations that feed the visit counter.
struct ShortcutsGuideView: View {
    var stepLabel = "Setup"
    @State private var appName = "Instagram"
    @State private var copied = false
    @Environment(\.openURL) private var openURL

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 8) {
                MonoLabel(stepLabel)
                Text("Tell me when you open it.")
                    .font(Typo.display(38))
                    .tracking(-1.1)
                    .fixedSize(horizontal: false, vertical: true)
                Text("iOS won't let apps watch each other, but Shortcuts can tap me on the shoulder. Two automations per app, about a minute each.")
                    .font(Typo.text(16))
                    .lineSpacing(3)
                    .foregroundStyle(Palette.body)
            }

            HStack(spacing: 10) {
                TextField("App name", text: $appName)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .font(Typo.text(16, weight: .semibold))
                    .padding(.horizontal, 16)
                    .frame(height: 48)
                    .card(radius: 24)
                Button(copied ? "Copied" : "Copy app name") {
                    UIPasteboard.general.string = appName
                    Settings.track(appName.trimmingCharacters(in: .whitespacesAndNewlines))
                    copied = true
                }
                .buttonStyle(PrimaryButtonStyle(height: 48))
                .frame(width: 160)
            }

            automation(number: 1, trigger: "Is Opened", action: "Log App Opened")
            automation(number: 2, trigger: "Is Closed", action: "Log App Closed")

            Button("Open Shortcuts") {
                if let url = URL(string: "shortcuts://") { openURL(url) }
            }
            .buttonStyle(SecondaryButtonStyle())

            infoNote("Repeat for every app you want to watch (YouTube, X, Reddit…). The name you type is the name you'll see in the counter. No Shortcuts yet? The debug panel in Settings can simulate opens and closes.")
        }
        .foregroundStyle(Palette.ink)
        .onChange(of: appName) { _, _ in copied = false }
    }

    private func automation(number: Int, trigger: String, action: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Automation \(number)").font(Typo.text(18, weight: .bold))
                Spacer()
                MonoLabel("When \(appName) \(trigger.lowercased())", size: 10)
            }
            VStack(alignment: .leading, spacing: 6) {
                stepLine("1", "Shortcuts › Automation › New Automation (+)")
                stepLine("2", "App › choose \(appName) › tick only \u{201C}\(trigger)\u{201D}")
                stepLine("3", "Pick \u{201C}Run Immediately\u{201D}, turn \u{201C}Notify When Run\u{201D} off › Next")
                stepLine("4", "New Blank Automation › Add Action › search \u{201C}\(action)\u{201D}")
                stepLine("5", "Tap App name and paste \u{201C}\(appName)\u{201D} › Done")
            }
        }
        .padding(EdgeInsets(top: 18, leading: 20, bottom: 18, trailing: 20))
        .frame(maxWidth: .infinity, alignment: .leading)
        .card(radius: 26)
    }

    private func stepLine(_ n: String, _ text: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Text(n).font(Typo.mono(12, weight: .medium)).foregroundStyle(Palette.accent)
            Text(text).font(Typo.text(15)).foregroundStyle(Palette.bodyDark)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}
