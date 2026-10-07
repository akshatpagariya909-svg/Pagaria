import SwiftUI

// Liquid Glass only on floating controls (tab bar, Live Activity, buttons).
// `.glassEffect` needs the iOS 26 SDK (Swift 6.2 / Xcode 26) to compile and iOS 26
// to run; older toolchains and OS versions get a plain material instead.

#if compiler(>=6.2)
extension View {
    /// Glass in `shape`, or `fallback` as a background on older systems.
    @ViewBuilder
    func floatingGlass<S: Shape>(
        _ shape: S, tint: Color? = nil, interactive: Bool = true,
        fallback: AnyShapeStyle = AnyShapeStyle(.ultraThinMaterial)
    ) -> some View {
        if #available(iOS 26.0, *) {
            self.glassEffect(Self.glass(tint: tint, interactive: interactive), in: shape)
        } else {
            self.background(fallback, in: shape)
        }
    }

    /// Glass in `shape`, or a custom fallback background view on older systems.
    @ViewBuilder
    func floatingGlass<S: Shape, F: View>(
        _ shape: S, tint: Color? = nil, interactive: Bool = true,
        @ViewBuilder fallbackView: () -> F
    ) -> some View {
        if #available(iOS 26.0, *) {
            self.glassEffect(Self.glass(tint: tint, interactive: interactive), in: shape)
        } else {
            self.background { fallbackView() }
        }
    }

    @available(iOS 26.0, *)
    private static func glass(tint: Color?, interactive: Bool) -> Glass {
        var glass = Glass.regular
        if let tint { glass = glass.tint(tint) }
        return interactive ? glass.interactive() : glass
    }
}
#else
extension View {
    func floatingGlass<S: Shape>(
        _ shape: S, tint: Color? = nil, interactive: Bool = true,
        fallback: AnyShapeStyle = AnyShapeStyle(.ultraThinMaterial)
    ) -> some View {
        self.background(fallback, in: shape)
    }

    func floatingGlass<S: Shape, F: View>(
        _ shape: S, tint: Color? = nil, interactive: Bool = true,
        @ViewBuilder fallbackView: () -> F
    ) -> some View {
        self.background { fallbackView() }
    }
}
#endif
