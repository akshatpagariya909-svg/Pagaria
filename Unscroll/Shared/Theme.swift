import SwiftUI
import UIKit

/// Colours from the approved designs (design/*.dc.html).
enum Palette {
    static let background = Color(hex: 0xF1EADF)
    static let card = Color(hex: 0xFBF7F0)
    static let ink = Color(hex: 0x221B16)
    static let accent = Color(hex: 0xC2471F)
    static let moss = Color(hex: 0x4F5B2E)

    static let border = Color(hex: 0xDDD2C1)
    static let muted = Color(hex: 0x6B5E52)      // mono labels
    static let secondary = Color(hex: 0x5B4F44)  // tile captions
    static let body = Color(hex: 0x4A3F36)       // body copy
    static let bodyDark = Color(hex: 0x3A3029)
    static let track = Color(hex: 0xEADFCF)
    static let amber = Color(hex: 0xB07A1E)
    static let selected = Color(hex: 0xFFF6EE)
    static let info = Color(hex: 0xE4D9C7)

    // Dark odometer card
    static let darkLabel = Color(hex: 0xC9BBA8)
    static let darkBody = Color(hex: 0xE3D7C7)
    static let peach = Color(hex: 0xE9A184)
    static let darkTrack = Color(hex: 0x3A2F28)

    // Receipt
    static let receiptDash = Color(hex: 0x9C8E7E)
    static let paper = Color(hex: 0xF4EEDD)

    // Shield
    static let shieldBackground = Color(hex: 0xCDB79B)
}

enum UIPalette {
    static let background = UIColor(hex: 0xF1EADF)
    static let card = UIColor(hex: 0xFBF7F0)
    static let ink = UIColor(hex: 0x221B16)
    static let accent = UIColor(hex: 0xC2471F)
    static let body = UIColor(hex: 0x4A3F36)
    static let shieldBackground = UIColor(hex: 0xCDB79B)
}

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }
}

extension UIColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1) {
        self.init(
            red: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: alpha
        )
    }
}

/// Type scale. The mockups use Bricolage Grotesque + IBM Plex Mono; natively
/// that maps to SF Rounded (heavy) for display and SF Mono for labels.
enum Typo {
    static func display(_ size: CGFloat, weight: Font.Weight = .heavy) -> Font {
        .system(size: size, weight: weight, design: .rounded)
    }
    static func text(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .rounded)
    }
    static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
}
