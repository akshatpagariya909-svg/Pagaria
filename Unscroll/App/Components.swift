import SwiftUI

/// Uppercase mono label ("THUMB ODOMETER", "STEP 2 OF 4").
struct MonoLabel: View {
    var text: String
    var color: Color = Palette.muted
    var size: CGFloat = 12

    init(_ text: String, color: Color = Palette.muted, size: CGFloat = 12) {
        self.text = text
        self.color = color
        self.size = size
    }

    var body: some View {
        Text(text.uppercased())
            .font(Typo.mono(size))
            .tracking(size * 0.08)
            .foregroundStyle(color)
    }
}

extension View {
    /// Cream card with the hairline border from the mockups.
    func card(radius: CGFloat = 26, fill: Color = Palette.card, border: Color? = Palette.border) -> some View {
        let shape = RoundedRectangle(cornerRadius: radius, style: .continuous)
        return self
            .background(fill, in: shape)
            .overlay { if let border { shape.strokeBorder(border, lineWidth: 1) } }
    }

    func screenBackground(_ color: Color = Palette.background) -> some View {
        self.background(color.ignoresSafeArea())
    }
}

/// Horizontal bar against a limit.
struct LimitBar: View {
    var fraction: Double
    var color: Color
    var track: Color = Palette.track
    var height: CGFloat = 8

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(track)
                Capsule().fill(color)
                    .frame(width: geo.size.width * min(1, max(0, fraction)))
            }
        }
        .frame(height: height)
    }
}

/// Big dark pill button (Continue, Close the app). Glass on iOS 26.
struct PrimaryButtonStyle: ButtonStyle {
    var fill: Color = Palette.ink
    var text: Color = Palette.card
    var height: CGFloat = 56

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Typo.text(17, weight: .bold))
            .foregroundStyle(text)
            .frame(maxWidth: .infinity, minHeight: height)
            .contentShape(Capsule())
            .floatingGlass(Capsule(), tint: fill, fallback: AnyShapeStyle(fill))
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

/// Outlined pill button (secondary actions).
struct SecondaryButtonStyle: ButtonStyle {
    var text: Color = Palette.ink
    var stroke: Color = Palette.ink.opacity(0.25)
    var height: CGFloat = 48

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Typo.text(15, weight: .semibold))
            .foregroundStyle(text)
            .frame(maxWidth: .infinity, minHeight: height)
            .contentShape(Capsule())
            .floatingGlass(Capsule(), fallback: AnyShapeStyle(Color.white.opacity(0.35)))
            .overlay(Capsule().strokeBorder(stroke, lineWidth: 1))
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

/// Round 44 pt icon button (settings shortcut on Today).
struct CircleIconButton: View {
    var systemName: String
    var label: String
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 18, weight: .medium))
                .foregroundStyle(Palette.ink)
                .frame(width: 44, height: 44)
                .floatingGlass(Circle(), fallback: AnyShapeStyle(Palette.card))
                .overlay(Circle().strokeBorder(Palette.border, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
    }
}

/// The little speaking avatar next to voice lines.
struct VoiceAvatar: View {
    var size: CGFloat = 36

    var body: some View {
        Image(systemName: "face.smiling")
            .font(.system(size: size * 0.5, weight: .semibold))
            .foregroundStyle(Color(hex: 0xFFF8F0))
            .frame(width: size, height: size)
            .background(Palette.accent, in: Circle())
            .accessibilityHidden(true)
    }
}

/// One-pixel dashed rule used on the receipt.
struct DashedRule: View {
    var color: Color = Palette.receiptDash

    var body: some View {
        GeometryReader { geo in
            Path { p in
                p.move(to: CGPoint(x: 0, y: 0.75))
                p.addLine(to: CGPoint(x: geo.size.width, y: 0.75))
            }
            .stroke(color, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4]))
        }
        .frame(height: 1.5)
    }
}

/// UIKit share sheet for files (CSV export).
struct ActivityView: UIViewControllerRepresentable {
    var items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}
