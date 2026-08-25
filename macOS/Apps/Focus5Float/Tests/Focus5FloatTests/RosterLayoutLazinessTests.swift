import XCTest
import SwiftUI
import AppKit
@testable import Focus5Float

/// Regression guard: `RosterLayout` must stay LAZY in both branches.
///
/// It carries two very different feeds. The repo board is five cards, where
/// eager layout is invisible. The Prompt Log is thousands of entries, each with
/// NSView-backed buttons, and realizing them all locks the main thread — the app
/// beach-balled on switching to that tab because the stacked branch had been
/// written as a plain `VStack`.
///
/// Laziness is not directly observable, so this measures its consequence: with a
/// lazy container, build+layout cost must not scale with row count. The
/// thresholds are deliberately loose — this catches "renders all 1,500", not a
/// modest slowdown, so it should not go flaky on a busy machine.
@MainActor
final class RosterLayoutLazinessTests: XCTestCase {

    private func entries(_ n: Int) -> [PromptLogEntry] {
        (0..<n).map {
            PromptLogEntry(repo: "repo-\($0 % 7)",
                           timestamp: "2026-08-24 19:57:39 PDT",
                           machine: "noel's Mac Studio",
                           branch: "development",
                           prompt: "a realistic prompt body for entry number \($0), long enough to wrap")
        }
    }

    private func layoutSeconds(rows: Int, tiled: Bool) -> Double {
        let view = ScrollView {
            RosterLayout(tiled: tiled) {
                ForEach(entries(rows)) { entry in
                    PromptLogRowView(entry: entry, isPinned: false, onTogglePin: {})
                }
            }
        }
        .frame(width: 380, height: 700)

        let start = Date()
        let host = NSHostingView(rootView: view)
        host.frame = NSRect(x: 0, y: 0, width: 380, height: 700)
        host.layoutSubtreeIfNeeded()
        return Date().timeIntervalSince(start)
    }

    func testTheStackedFeedDoesNotRealizeEveryRow() {
        let small = layoutSeconds(rows: 20, tiled: false)
        let large = layoutSeconds(rows: 1_500, tiled: false)

        XCTAssertLessThan(
            large, max(small * 20, 2.0),
            """
            Laying out 1,500 stacked rows cost \(String(format: "%.2f", large))s against \
            \(String(format: "%.2f", small))s for 20 — the container is realizing every row \
            instead of only the visible ones. This is what beach-balls the Prompt Log tab.
            """
        )
    }

    func testTheTiledFeedDoesNotRealizeEveryRow() {
        let small = layoutSeconds(rows: 20, tiled: true)
        let large = layoutSeconds(rows: 1_500, tiled: true)

        XCTAssertLessThan(large, max(small * 20, 2.0),
                          "Tiled layout of 1,500 rows cost \(String(format: "%.2f", large))s.")
    }
}
