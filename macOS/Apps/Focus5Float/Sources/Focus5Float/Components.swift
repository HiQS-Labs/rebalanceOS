import SwiftUI

// Harvested from TextReplacementStudio/Views/StudioComponents.swift — the
// `import TextReplacementCore` dependency was dropped (these use only SwiftUI +
// Theme). KeyCap → position badge; GroupTag → branch/tag chip; StatusDot is new
// for the Focus 5 health signal.

/// Monospaced key-cap: text in SF Mono inside a rounded fill with a hairline
/// border and a 1px bottom highlight. Used here for the `#1`…`#5` position badge.
struct KeyCap: View {
    let text: String
    var font: Font = Theme.mono
    var paddingH: CGFloat = 7
    var height: CGFloat = 23

    var body: some View {
        Text(text)
            .font(font)
            .foregroundStyle(Theme.text)
            .lineLimit(1)
            .fixedSize()
            .padding(.horizontal, paddingH)
            .frame(height: height)
            .background(Theme.keycapBG, in: RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .strokeBorder(Theme.keycapBorder, lineWidth: 1)
            )
            .shadow(color: Theme.keycapShadow, radius: 0, x: 0, y: 1)
    }
}

/// Group/branch chip: a colored dot + a label in a soft capsule.
struct GroupTag: View {
    let name: String

    var body: some View {
        HStack(spacing: 5) {
            Circle()
                .fill(Theme.groupColor(name))
                .frame(width: 7, height: 7)
            Text(name)
                .font(Theme.monoSmall)
                .foregroundStyle(Theme.text2)
                .lineLimit(1)
        }
        .padding(.vertical, 3)
        .padding(.leading, 7)
        .padding(.trailing, 8)
        .background(Theme.hover, in: RoundedRectangle(cornerRadius: 7, style: .continuous))
    }
}

/// Overall roster-health rollup colour. `dirty` is the count of dirty roster
/// repos (shown as "Status: N", so all-clean reads "Status: 0").
/// green = none dirty · red = all dirty · orange = some dirty.
enum RosterHealth {
    static func tint(dirty: Int, total: Int) -> Color {
        if dirty == 0 { return Theme.diffAdd }       // green — all clean
        if dirty >= total { return Theme.diffRemove } // red — all dirty
        return .orange                                // some dirty
    }
}

/// Tree-health dot: green = clean, red = dirty/needs attention, grey = no signal.
/// Color is never the only cue — callers pair it with adjacent text.
struct StatusDot: View {
    let isDirty: Bool
    let healthAvailable: Bool

    private var color: Color {
        guard healthAvailable else { return Theme.text3 }
        return isDirty ? Theme.diffRemove : Theme.diffAdd
    }

    var body: some View {
        Circle().fill(color).frame(width: 11, height: 11)
            .accessibilityLabel(healthAvailable ? (isDirty ? "dirty" : "clean") : "unavailable")
    }
}

/// Hover tooltip drawn by SwiftUI itself. AppKit `.help()` tooltips only appear
/// while the app is active, and this panel never activates the app
/// (`.nonactivatingPanel` + `orderFrontRegardless`), so `.help()` text never
/// shows on hover. The tip is a dark bubble below the control with an arrow
/// pointing up at the control's centre. `edge` picks which side of the control
/// the bubble lines up with, so bubbles near the panel edge aren't clipped; the
/// arrow stays centred on the control either way. Callers must keep the
/// control's container above later siblings (`zIndex`), or the content below
/// will draw over the tip.
struct HoverTooltip: ViewModifier {
    let text: String
    let edge: HorizontalAlignment

    /// How long the pointer must rest on the control before the tip shows.
    static let dwell: TimeInterval = 0.5

    @State private var state: HoverTooltipState

    private let gap: CGFloat = 4
    private let arrowSize = CGSize(width: 12, height: 6)

    /// `state` lets tests render the tip already shown; callers use the default.
    init(text: String, edge: HorizontalAlignment, state: HoverTooltipState = HoverTooltipState()) {
        self.text = text
        self.edge = edge
        _state = State(initialValue: state)
    }

    func body(content: Content) -> some View {
        content
            .onHover { inside in
                guard inside else {
                    state.pointerExited()
                    return
                }
                let hover = state.pointerEntered()
                DispatchQueue.main.asyncAfter(deadline: .now() + Self.dwell) {
                    state.dwellElapsed(for: hover)
                }
            }
            .overlay(alignment: .topLeading) {
                if showing {
                    // Measure the control, then hang the tip below it: the
                    // arrow stays centred on the control and the bubble lines
                    // up with `edge`. The tip's top starts `gap` below the
                    // control's bottom edge, so it never covers the control.
                    GeometryReader { geo in
                        VStack(alignment: edge, spacing: -0.5) {
                            TooltipArrow()
                                .fill(Theme.tooltipBG)
                                .frame(width: arrowSize.width, height: arrowSize.height)
                                .frame(width: geo.size.width)
                            Text(text)
                                .font(Theme.bodyMed)
                                .foregroundStyle(Theme.tooltipText)
                                .lineLimit(1)
                                .fixedSize()
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(Theme.tooltipBG, in: RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous))
                        }
                        .fixedSize()
                        .frame(width: geo.size.width, alignment: Alignment(horizontal: edge, vertical: .top))
                        .offset(y: geo.size.height + gap)
                    }
                    .tooltipChrome()
                }
            }
            .animation(.easeOut(duration: 0.12), value: state.isVisible)
    }

    private var showing: Bool { state.isVisible && !text.isEmpty }
}

/// The show/hide rules behind `HoverTooltip`, kept apart from the view so they
/// can be tested without a pointer. Every enter and exit starts a new hover;
/// the dwell timer started on entry passes back the hover it belongs to, and
/// only reveals the tip if that hover is still the current one. Without that
/// check, a timer left over from an earlier hover (enter, leave after 0.2 s,
/// come back) would show the tip before the new hover had dwelt for the full
/// delay.
struct HoverTooltipState: Equatable {
    private(set) var isVisible = false
    private var hover = 0
    private var inside = false

    /// The pointer entered the control. Returns the hover to hand back to
    /// `dwellElapsed(for:)` once the dwell delay has passed.
    mutating func pointerEntered() -> Int {
        hover += 1
        inside = true
        isVisible = false
        return hover
    }

    /// The pointer left the control: hide the tip and orphan any pending dwell.
    mutating func pointerExited() {
        hover += 1
        inside = false
        isVisible = false
    }

    /// A dwell delay started for `hover` has passed.
    mutating func dwellElapsed(for hover: Int) {
        guard inside, hover == self.hover else { return }
        isVisible = true
    }
}

/// Upward-pointing triangle joining a tooltip bubble to its control.
private struct TooltipArrow: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.midX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
        path.closeSubpath()
        return path
    }
}

private extension View {
    /// Shared tooltip treatment: soft shadow, no hit-testing, fade, and hidden
    /// from VoiceOver (the control carries its own accessibility label).
    func tooltipChrome() -> some View {
        shadow(color: .black.opacity(0.22), radius: 6, x: 0, y: 2)
            .allowsHitTesting(false)
            .transition(.opacity)
            .accessibilityHidden(true)
    }
}

extension View {
    /// Tooltip that shows on hover even though the panel never activates the app.
    func hoverTooltip(_ text: String, edge: HorizontalAlignment = .center) -> some View {
        modifier(HoverTooltip(text: text, edge: edge))
    }
}

/// Telemetry health dot: maps HealthStatus directly to green / orange / red.
/// Color is never the only cue — callers pair it with adjacent text.
struct HealthDot: View {
    let health: HealthStatus

    private var color: Color {
        switch health {
        case .green:  return Theme.diffAdd
        case .orange: return .orange
        case .red:    return Theme.diffRemove
        }
    }

    var body: some View {
        Circle().fill(color).frame(width: 10, height: 10)
            .accessibilityLabel(health.rawValue)
    }
}
