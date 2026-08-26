import XCTest
import SwiftUI
import AppKit
@testable import Focus5Float

/// GH-120 — the Focus 5 board's responsive card tiling, ported from the web.
///
/// These measure the REAL layout type at REAL panel widths rather than asserting
/// on source shape, because the two bugs this feature already shipped were both
/// invisible to a source-level check:
///
///   1. A dead control. The first cut gated the reflow on `ViewThatFits`, which
///      compares a candidate's IDEAL width; a column of unwrapped `Text` ideals
///      out at its longest line (measured: ~993pt against ~300pt on offer), so
///      the row candidate never won and the toggle rendered identically both
///      ways at every width.
///   2. Reflowing the wrong thing — the sections INSIDE a card rather than the
///      cards themselves.
///
/// So: assert that widening actually buys columns, that the toggle actually
/// changes the render, and (agy's catch during the GH-120 consult) that a wide
/// layout is not "succeeding" by squeezing cards into unreadable slivers — a
/// height comparison alone would pass a row of truncated stubs.
@MainActor
final class RosterLayoutRenderTests: XCTestCase {

    /// Realistic copy — a card that renders an empty rank reason and no activity
    /// would understate how much width the real board needs.
    private func cards(_ n: Int) -> [RepoCard] {
        (1...n).map { i in
            let json = """
            {"position":\(i),"repo_name":"repo-number-\(i)",
             "local_path":"/repos/repo-number-\(i)",
             "vscode_url":"vscode://file/repos/repo-number-\(i)",
             "rank_reason":"3 unpushed commits and a dirty tree since 2026-08-19",
             "ranking_mode":"recent_activity","computed_at":"2026-01-01T00:00:00Z",
             "ahead":3,"behind":0,"modified_count":2,"untracked_count":1,"is_dirty":true,
             "health_available":true,"recent_activity":[]}
            """
            return try! Focus5JSON.decoder().decode(RepoCard.self, from: Data(json.utf8))
        }
    }

    @ViewBuilder private func roster(_ n: Int, tiled: Bool) -> some View {
        RosterLayout(tiled: tiled) {
            ForEach(Array(cards(n).enumerated()), id: \.element.id) { index, card in
                RepoCardView(card: card, darker: !index.isMultiple(of: 2))
            }
        }
    }

    private func height(_ n: Int, tiled: Bool, width: CGFloat) -> CGFloat {
        NSHostingView(rootView: roster(n, tiled: tiled).frame(width: width)).fittingSize.height
    }

    /// The web board's own breakpoints, which this is a port of: 5 columns above
    /// 1400px, 3 above 1000, 2 above 680, 1 below. Same widths must buy at least
    /// as many columns here, or the two surfaces have silently diverged.
    func testWideningThePanelBuysColumnsTheWayTheWebBoardDoes() {
        // 5 cards: 1 row at 1400 (5 columns), 2 rows at 1000 (3), 5 rows at 340 (1).
        // Fewer rows means shorter, so height must fall strictly as width grows.
        let wide = height(5, tiled: true, width: 1400)
        let mid = height(5, tiled: true, width: 1000)
        let narrow = height(5, tiled: true, width: 340)

        XCTAssertLessThan(wide, mid, "1400pt fitted no more columns than 1000pt.")
        XCTAssertLessThan(mid, narrow, "1000pt fitted no more columns than a 340pt panel.")
    }

    func testTheDefaultPanelWidthStacksExactlyAsItAlwaysHas() {
        // 340pt fits one 280pt card, so tiled and stacked must agree there. This
        // is what makes tiling safe to default ON: it costs nothing until the
        // operator widens the panel.
        XCTAssertEqual(height(5, tiled: true, width: 340),
                       height(5, tiled: false, width: 340),
                       accuracy: 1.0,
                       "Tiling changed the default-width render; it should be a no-op at 340pt.")
    }

    func testTheToggleIsNotADeadControlWhereItMatters() {
        // At a width that fits several columns, the two states MUST differ —
        // this is the assertion the ViewThatFits version failed.
        XCTAssertNotEqual(height(5, tiled: true, width: 1400),
                          height(5, tiled: false, width: 1400),
                          accuracy: 1.0,
                          "Tiled and stacked rendered identically at 1400pt — dead control.")
    }

    func testTilingNeverSqueezesCardsBelowAReadableWidth() {
        // agy's catch: a height-only assertion would pass a layout that "fits"
        // by shredding every card. Pin the floor instead of trusting height.
        XCTAssertGreaterThanOrEqual(
            RosterLayout<EmptyView>.minimumCardWidth, 260,
            "Minimum card width dropped below what a repo name and commit line need."
        )

        // And the grid must honour that floor: 5 cards at 900pt cannot be one row
        // (that would be 180pt each), so it must have wrapped to a second row and
        // therefore be taller than the same 5 cards at 1400pt.
        XCTAssertGreaterThan(
            height(5, tiled: true, width: 900),
            height(5, tiled: true, width: 1400),
            "900pt produced as few rows as 1400pt — cards were squeezed past the floor."
        )
    }

    func testASingleCardTakesOneColumnRatherThanTheWholePanel() {
        // Web parity: a lone card occupies one grid column, it does not stretch
        // across a 1400pt panel. A narrower card wraps its text more, so the
        // tiled render is TALLER — asserting equality here would actually be
        // asserting the card had gone full-bleed.
        XCTAssertGreaterThan(height(1, tiled: true, width: 1400),
                             height(1, tiled: false, width: 1400),
                             "A single tiled card stretched the full panel width.")
    }
}
