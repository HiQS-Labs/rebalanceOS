import XCTest
import SwiftUI
@testable import Focus5Float

/// Real assertions for the pure-function logic the old env-var self-tests
/// (`FOCUS5_HEALTHTEST`, `FOCUS5_VSCODETEST`) only smoke-checked by eyeballing
/// printed output. `swift test` gives these a pass/fail result and CI hookup.
final class PureLogicTests: XCTestCase {
    func testAppIconKeepsMacOSOpticalMargin() throws {
        let packageRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent() // Focus5FloatTests
            .deletingLastPathComponent() // Tests
            .deletingLastPathComponent() // package root
        let iconURL = packageRoot.appendingPathComponent("Resources/AppIcon.icns")

        let image = try XCTUnwrap(NSImage(contentsOf: iconURL))
        let tiff = try XCTUnwrap(image.tiffRepresentation)
        let bitmap = try XCTUnwrap(NSBitmapImageRep(data: tiff))
        XCTAssertEqual(bitmap.pixelsWide, 1024)
        XCTAssertEqual(bitmap.pixelsHigh, 1024)

        var minX = bitmap.pixelsWide
        var minY = bitmap.pixelsHigh
        var maxX = -1
        var maxY = -1
        for y in 0..<bitmap.pixelsHigh {
            for x in 0..<bitmap.pixelsWide
            where (bitmap.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0.01 {
                minX = min(minX, x)
                minY = min(minY, y)
                maxX = max(maxX, x)
                maxY = max(maxY, y)
            }
        }

        // ICON REGRESSION GUARD: macOS does not normalize full-bleed artwork;
        // without this optical margin Focus 5 looks larger than adjacent icons.
        XCTAssertEqual(NSRect(x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1),
                       NSRect(x: 100, y: 100, width: 824, height: 824))
    }

    @MainActor
    func testPanelHostingViewSuppressesHiddenTitlebarSafeArea() {
        let rect = NSRect(x: 0, y: 0, width: 340, height: 660)
        let hostingView = FirstMouseHostingView(rootView: Color.clear)
        hostingView.frame = rect

        let panel = FloatingPanel(
            contentRect: rect,
            styleMask: [.titled, .closable, .resizable, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.contentView = hostingView
        panel.contentView?.layoutSubtreeIfNeeded()

        XCTAssertEqual(
            hostingView.safeAreaInsets.top,
            0,
            "The hidden titlebar must not reintroduce a blank strip above the visible panel shell"
        )
        XCTAssertEqual(hostingView.safeAreaRect, hostingView.bounds)
    }

    func testPanelSizingCapsWidthWithoutCappingHeightToCurrentScreen() {
        XCTAssertEqual(PanelSizing.minimum, NSSize(width: 340, height: 360))
        XCTAssertEqual(PanelSizing.maximum.width, 420)
        XCTAssertEqual(
            PanelSizing.maximum.height,
            CGFloat(Float.greatestFiniteMagnitude),
            "Height must retain AppKit's default maximum so an offset autosaved frame can still grow upward"
        )
    }

    func testRosterHealthTint() {
        XCTAssertEqual(RosterHealth.tint(dirty: 0, total: 5), Theme.diffAdd)     // all clean → green
        XCTAssertEqual(RosterHealth.tint(dirty: 5, total: 5), Theme.diffRemove) // all dirty → red
        XCTAssertEqual(RosterHealth.tint(dirty: 2, total: 5), .orange)          // some dirty → orange
    }

    func testVSCodeLauncherArgumentsAreExactlyTheFolderNoFlags() {
        let argv = VSCodeLauncher.arguments(forRepoPath: "/repos/demo repo")
        XCTAssertEqual(argv, ["/repos/demo repo"])
    }

    func testVSCodeLauncherCandidateOrder() {
        XCTAssertEqual(VSCodeLauncher.candidates, [
            "/opt/homebrew/bin/code",
            "/usr/local/bin/code",
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
        ])
    }

    /// Mirrors focus5_scan.vscode_url()'s `f"vscode://file{quote(local_path, safe='/')}"`
    /// — same safe-char set (alnum + `_.-~/`), everything else percent-encoded.
    func testVSCodeLauncherFileURLMatchesServerEncoding() {
        XCTAssertEqual(
            VSCodeLauncher.fileURL(forLocalPath: "/Users/example/Projects/rebalance-OS"),
            "vscode://file/Users/example/Projects/rebalance-OS"
        )
        XCTAssertEqual(
            VSCodeLauncher.fileURL(forLocalPath: "/repos/demo repo"),
            "vscode://file/repos/demo%20repo"
        )
    }

    func testRelTimeAgoBuckets() {
        let now = Date()
        XCTAssertEqual(RelTime.ago(now.addingTimeInterval(-30), now: now), "just now")
        XCTAssertEqual(RelTime.ago(now.addingTimeInterval(-5 * 60), now: now), "5m ago")
        XCTAssertEqual(RelTime.ago(now.addingTimeInterval(-3 * 3600), now: now), "3h ago")
        XCTAssertEqual(RelTime.ago(now.addingTimeInterval(-2 * 86400), now: now), "2d ago")
        XCTAssertEqual(RelTime.ago(Date?.none), "")
    }

    func testRelTimeIsOlderThan() {
        let now = Date()
        let iso = ISO8601DateFormatter().string(from: now.addingTimeInterval(-25 * 3600))
        XCTAssertTrue(RelTime.isOlderThan(iso, hours: 24, now: now))
        XCTAssertFalse(RelTime.isOlderThan(iso, hours: 48, now: now))
        XCTAssertFalse(RelTime.isOlderThan(nil, hours: 24, now: now))
    }

    @MainActor
    func testHiddenReposExcludesFromVisibleRosterAndPushesUpList() {
        let key = "hiddenRepoNames"
        UserDefaults.standard.removeObject(forKey: key)
        defer { UserDefaults.standard.removeObject(forKey: key) }

        let model = Focus5Model()

        func makeCard(name: String, pos: Int) -> RepoCard {
            let json = """
            {"position":\(pos),"repo_name":"\(name)","local_path":"/repos/\(name)","vscode_url":"vscode://file/repos/\(name)",
             "rank_reason":"r","ranking_mode":"recent_activity","computed_at":"2026-01-01T00:00:00Z",
             "ahead":0,"behind":0,"modified_count":0,"untracked_count":0,"is_dirty":false,
             "health_available":true,"recent_activity":[]}
            """
            return try! Focus5JSON.decoder().decode(RepoCard.self, from: Data(json.utf8))
        }

        model.roster = [
            makeCard(name: "repo-A", pos: 1),
            makeCard(name: "repo-B", pos: 2),
            makeCard(name: "repo-C", pos: 3),
        ]

        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-A", "repo-B", "repo-C"])
        XCTAssertEqual(model.hiddenRosterCount, 0)
        XCTAssertFalse(model.hasHiddenRepos)

        // Hide repo-A: repo-B and repo-C must push up
        model.hideRepo("repo-A")
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-B", "repo-C"])
        XCTAssertEqual(model.hiddenRosterCount, 1)
        XCTAssertTrue(model.hasHiddenRepos)

        // Test persistence across model reload
        let model2 = Focus5Model()
        model2.roster = model.roster
        XCTAssertEqual(model2.visibleRoster.map(\.repoName), ["repo-B", "repo-C"])
        XCTAssertTrue(model2.isRepoHidden("repo-a")) // case-insensitive canonical key match

        // Restore all repos
        model2.unhideAllRepos()
        XCTAssertEqual(model2.visibleRoster.map(\.repoName), ["repo-A", "repo-B", "repo-C"])
        XCTAssertEqual(model2.hiddenRosterCount, 0)
        XCTAssertFalse(model2.hasHiddenRepos)
    }

    @MainActor
    func testCandidatePromotionWhenRepoIsHidden() {
        let key = "hiddenRepoNames"
        UserDefaults.standard.removeObject(forKey: key)
        defer { UserDefaults.standard.removeObject(forKey: key) }

        let model = Focus5Model()

        func makeCard(name: String, pos: Int) -> RepoCard {
            let json = """
            {"position":\(pos),"repo_name":"\(name)","local_path":"/repos/\(name)","vscode_url":"vscode://file/repos/\(name)",
             "rank_reason":"r","ranking_mode":"recent_activity","computed_at":"2026-01-01T00:00:00Z",
             "ahead":0,"behind":0,"modified_count":0,"untracked_count":0,"is_dirty":false,
             "health_available":true,"recent_activity":[]}
            """
            return try! Focus5JSON.decoder().decode(RepoCard.self, from: Data(json.utf8))
        }

        func makeWarning(name: String) -> OffRosterWarning {
            let json = """
            {"repo_name":"\(name)","local_path":"/repos/\(name)","ahead":1,"modified_count":2,"untracked_count":0,"is_dirty":true,"warning_reason":"ahead"}
            """
            return try! Focus5JSON.decoder().decode(OffRosterWarning.self, from: Data(json.utf8))
        }

        model.roster = [
            makeCard(name: "repo-1", pos: 1),
            makeCard(name: "repo-2", pos: 2),
            makeCard(name: "repo-3", pos: 3),
            makeCard(name: "repo-4", pos: 4),
            makeCard(name: "repo-5", pos: 5),
        ]
        model.offRoster = [
            makeWarning(name: "off-6"),
            makeWarning(name: "off-7"),
        ]

        // Initial state: full roster of 5, 2 off-roster warnings
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-1", "repo-2", "repo-3", "repo-4", "repo-5"])
        XCTAssertEqual(model.visibleOffRoster.map(\.repoName), ["off-6", "off-7"])
        XCTAssertTrue(model.promotedCards.isEmpty)

        // Hide repo-2: repo-3, repo-4, repo-5 push up, and off-6 is promoted to 5th position
        model.hideRepo("repo-2")
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-1", "repo-3", "repo-4", "repo-5", "off-6"])
        XCTAssertEqual(model.visibleRoster.last?.position, 5)
        XCTAssertEqual(model.visibleOffRoster.map(\.repoName), ["off-7"])

        // Hide repo-4: off-7 is now promoted as well
        model.hideRepo("repo-4")
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-1", "repo-3", "repo-5", "off-6", "off-7"])
        XCTAssertTrue(model.visibleOffRoster.isEmpty)

        // Hide promoted off-6: off-roster is exhausted, visible roster drops to 4
        model.hideRepo("off-6")
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-1", "repo-3", "repo-5", "off-7"])

        // Unhide all: restores original 5, puts off-roster items back in off-roster
        model.unhideAllRepos()
        XCTAssertEqual(model.visibleRoster.map(\.repoName), ["repo-1", "repo-2", "repo-3", "repo-4", "repo-5"])
        XCTAssertEqual(model.visibleOffRoster.map(\.repoName), ["off-6", "off-7"])
        XCTAssertTrue(model.promotedCards.isEmpty)
    }
}
