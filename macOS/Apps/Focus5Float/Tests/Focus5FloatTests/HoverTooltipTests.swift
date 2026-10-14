import XCTest
import SwiftUI
import AppKit
@testable import Focus5Float

/// The panel's hover tooltips (PR #324). The panel never activates the app, so
/// AppKit `.help()` tooltips never appear; `HoverTooltip` draws its own.
///
/// Two halves:
///   1. The show/hide rules, driven through `HoverTooltipState` directly —
///      including the stale-timer case (enter, leave, re-enter before the first
///      dwell ends) that showed the tip early.
///   2. The rendered tip, read back as pixels. These run in the test process,
///      which is never the active app, so they also witness that the tip draws
///      without activation — the AppKit boundary `.help()` failed at. They do
///      not synthesize pointer events.
final class HoverTooltipStateTests: XCTestCase {

    func testTipStaysHiddenUntilTheDwellEnds() {
        var state = HoverTooltipState()
        _ = state.pointerEntered()
        XCTAssertFalse(state.isVisible, "Tip showed on entry, before the dwell delay.")
    }

    func testTipShowsAfterTheDwell() {
        var state = HoverTooltipState()
        let hover = state.pointerEntered()
        state.dwellElapsed(for: hover)
        XCTAssertTrue(state.isVisible)
    }

    func testTipHidesWhenThePointerLeaves() {
        var state = HoverTooltipState()
        let hover = state.pointerEntered()
        state.dwellElapsed(for: hover)
        state.pointerExited()
        XCTAssertFalse(state.isVisible)
    }

    func testLeavingBeforeTheDwellEndsNeverShowsTheTip() {
        var state = HoverTooltipState()
        let hover = state.pointerEntered()
        state.pointerExited()
        state.dwellElapsed(for: hover)
        XCTAssertFalse(state.isVisible, "A dwell that finished after the pointer left showed the tip.")
    }

    func testATimerFromAnEarlierHoverCannotShowTheTipEarly() {
        // Enter, leave after 0.2 s, come back after another 0.2 s: the first
        // hover's timer fires while the pointer is inside again, 0.1 s into the
        // new hover. It belongs to the old hover and must not show the tip.
        var state = HoverTooltipState()
        let first = state.pointerEntered()
        state.pointerExited()
        let second = state.pointerEntered()

        state.dwellElapsed(for: first)
        XCTAssertFalse(state.isVisible, "The earlier hover's timer showed the tip before the new dwell ended.")

        state.dwellElapsed(for: second)
        XCTAssertTrue(state.isVisible, "The current hover's own dwell did not show the tip.")
    }
}

@MainActor
final class HoverTooltipRenderTests: XCTestCase {

    private let canvas = CGSize(width: 240, height: 120)
    private let icon = CGRect(x: 106, y: 10, width: 28, height: 28)

    /// The tip as a hover that has dwelt would leave it.
    private var shown: HoverTooltipState {
        var state = HoverTooltipState()
        let hover = state.pointerEntered()
        state.dwellElapsed(for: hover)
        return state
    }

    /// A solid red stand-in for a toolbar icon, with a shown tip, on white.
    private func render(edge: HorizontalAlignment, text: String = "Tile the repos left to right") -> Pixels {
        let view = Rectangle()
            .fill(Color.red)
            .frame(width: icon.width, height: icon.height)
            .modifier(HoverTooltip(text: text, edge: edge, state: shown))
            .padding(.leading, icon.minX)
            .padding(.top, icon.minY)
            .frame(width: canvas.width, height: canvas.height, alignment: .topLeading)
            .background(Color.white)
            .environment(\.colorScheme, .light)
        let renderer = ImageRenderer(content: view)
        renderer.scale = 1
        guard let image = renderer.cgImage else {
            XCTFail("ImageRenderer produced no image")
            return Pixels(width: 0, height: 0, rgba: [])
        }
        return Pixels(image)
    }

    func testTheTipNeverCoversTheIcon() {
        for edge in [HorizontalAlignment.leading, .center, .trailing] {
            let pixels = render(edge: edge)
            let covered = pixels.points(in: icon.insetBy(dx: 1, dy: 1)).filter { !pixels.isRed($0) }
            XCTAssertTrue(covered.isEmpty, "\(edge) tip drew over \(covered.count) icon pixels.")
        }
    }

    func testTheTipHangsBelowTheIcon() {
        for edge in [HorizontalAlignment.leading, .center, .trailing] {
            let pixels = render(edge: edge)
            let tip = pixels.darkPoints()
            XCTAssertFalse(tip.isEmpty, "\(edge) tip did not render.")
            XCTAssertTrue(tip.allSatisfy { $0.y >= icon.maxY }, "\(edge) tip drew above the icon's bottom edge.")
        }
    }

    func testEdgeKeepsTheBubbleOnTheRequestedSide() {
        let leading = render(edge: .leading).darkPoints()
        XCTAssertGreaterThanOrEqual(leading.map(\.x).min() ?? -1, icon.minX - 1,
                                    "A leading tip spilled left of the icon, toward the panel's left edge.")

        let trailing = render(edge: .trailing).darkPoints()
        XCTAssertLessThanOrEqual(trailing.map(\.x).max() ?? .infinity, icon.maxX + 1,
                                 "A trailing tip spilled right of the icon, toward the panel's right edge.")

        let centred = render(edge: .center).darkPoints()
        XCTAssertLessThan(centred.map(\.x).min() ?? .infinity, icon.minX, "A centred tip did not extend left of the icon.")
        XCTAssertGreaterThan(centred.map(\.x).max() ?? -1, icon.maxX, "A centred tip did not extend right of the icon.")
    }

    func testAHiddenTipDrawsNothing() {
        let view = Rectangle()
            .fill(Color.red)
            .frame(width: icon.width, height: icon.height)
            .modifier(HoverTooltip(text: "Hide panel", edge: .center))
            .padding(.leading, icon.minX)
            .padding(.top, icon.minY)
            .frame(width: canvas.width, height: canvas.height, alignment: .topLeading)
            .background(Color.white)
        let renderer = ImageRenderer(content: view)
        renderer.scale = 1
        guard let image = renderer.cgImage else { return XCTFail("ImageRenderer produced no image") }
        XCTAssertTrue(Pixels(image).darkPoints().isEmpty, "A tip drew before any hover.")
    }
}

/// RGBA8 pixels of a rendered image, top row first.
private struct Pixels {
    let width: Int
    let height: Int
    let rgba: [UInt8]

    init(width: Int, height: Int, rgba: [UInt8]) {
        self.width = width
        self.height = height
        self.rgba = rgba
    }

    init(_ image: CGImage) {
        let w = image.width, h = image.height
        var data = [UInt8](repeating: 0, count: w * h * 4)
        data.withUnsafeMutableBytes { buffer in
            let context = CGContext(
                data: buffer.baseAddress, width: w, height: h,
                bitsPerComponent: 8, bytesPerRow: w * 4,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            )
            context?.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
        }
        self.init(width: w, height: h, rgba: data)
    }

    private func rgb(_ p: CGPoint) -> (r: Int, g: Int, b: Int) {
        let i = (Int(p.y) * width + Int(p.x)) * 4
        return (Int(rgba[i]), Int(rgba[i + 1]), Int(rgba[i + 2]))
    }

    func points(in rect: CGRect) -> [CGPoint] {
        let xs = max(0, Int(rect.minX))..<min(width, Int(rect.maxX))
        let ys = max(0, Int(rect.minY))..<min(height, Int(rect.maxY))
        return ys.flatMap { y in xs.map { x in CGPoint(x: x, y: y) } }
    }

    func isRed(_ p: CGPoint) -> Bool {
        let c = rgb(p)
        return c.r > 200 && c.g < 80 && c.b < 80
    }

    /// The tooltip bubble's fill. Dark enough to exclude the soft shadow, which
    /// only tints the white background grey.
    func darkPoints() -> [CGPoint] {
        points(in: CGRect(x: 0, y: 0, width: width, height: height)).filter {
            let c = rgb($0)
            return max(c.r, c.g, c.b) < 100
        }
    }
}
