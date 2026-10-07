import SwiftUI
import WidgetKit

@main
struct UnscrollWidgetsBundle: WidgetBundle {
    var body: some Widget {
        VisitsWidget()
        OdometerWidget()
        LimitCircularWidget()
        VisitsRectangularWidget()
        SessionLiveActivity()
    }
}
