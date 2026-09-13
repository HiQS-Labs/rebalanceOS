import XCTest
@testable import Focus5Float

final class RecentGitHubItemsTests: XCTestCase {
    func testDecodesRecentIssuesAndPRsFromJSON() throws {
        let json = """
        {
            "position": 1,
            "repo_name": "AI-DDTK",
            "repo_full_name": "Hypercart-Dev-Tools/AI-DDTK-Fix-Iterate-Loop",
            "local_path": "/Users/test/AI-DDTK",
            "remote_url": "https://github.com/Hypercart-Dev-Tools/AI-DDTK-Fix-Iterate-Loop",
            "vscode_url": "vscode://file/Users/test/AI-DDTK",
            "rank_reason": "active",
            "ranking_mode": "recent_activity",
            "computed_at": "2026-09-10T23:00:00Z",
            "branch": "development",
            "ahead": 0,
            "behind": 0,
            "modified_count": 0,
            "untracked_count": 0,
            "is_dirty": false,
            "health_available": true,
            "recent_activity": [],
            "recent_issues": [
                {"number": 130, "html_url": "https://github.com/test/130", "title": "Issue 130"},
                {"number": 125, "html_url": "https://github.com/test/125", "title": "Issue 125"},
                {"number": 123, "html_url": "https://github.com/test/123", "title": "Issue 123"}
            ],
            "recent_prs": [
                {"number": 142, "html_url": "https://github.com/test/142", "title": "PR 142"},
                {"number": 140, "html_url": "https://github.com/test/140", "title": "PR 140"}
            ]
        }
        """

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let card = try decoder.decode(RepoCard.self, from: json.data(using: .utf8)!)

        XCTAssertTrue(card.hasRecentGitHubItems)
        XCTAssertEqual(card.issues.count, 3)
        XCTAssertEqual(card.prs.count, 2)
        XCTAssertEqual(card.issues.map(\.number), [130, 125, 123])
        XCTAssertEqual(card.prs.map(\.number), [142, 140])
        XCTAssertEqual(card.issues[0].htmlUrl, "https://github.com/test/130")
        XCTAssertEqual(card.prs[0].htmlUrl, "https://github.com/test/142")
    }

    func testHandlesMissingRecentItemsGracefully() throws {
        let json = """
        {
            "position": 1,
            "repo_name": "local-repo",
            "local_path": "/Users/test/local-repo",
            "vscode_url": "vscode://file/Users/test/local-repo",
            "rank_reason": "active",
            "ranking_mode": "recent_activity",
            "computed_at": "2026-09-10T23:00:00Z",
            "ahead": 0,
            "behind": 0,
            "modified_count": 0,
            "untracked_count": 0,
            "is_dirty": false,
            "health_available": true,
            "recent_activity": []
        }
        """

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let card = try decoder.decode(RepoCard.self, from: json.data(using: .utf8)!)

        XCTAssertFalse(card.hasRecentGitHubItems)
        XCTAssertEqual(card.issues, [])
        XCTAssertEqual(card.prs, [])
    }

    func testCopyWithPreservesRecentGitHubItems() {
        let issue = GitHubItemRef(number: 42, htmlUrl: "https://github.com/test/42", title: "Test")
        let pr = GitHubItemRef(number: 99, htmlUrl: "https://github.com/test/99", title: "Test PR")

        let card = RepoCard(
            position: 1,
            repoName: "test",
            repoFullName: "owner/test",
            localPath: "/test",
            remoteUrl: nil,
            vscodeUrl: "vscode://file/test",
            rankReason: "test",
            rankingMode: "recent_activity",
            computedAt: "",
            branch: nil,
            upstream: nil,
            hasUpstream: nil,
            ahead: 0,
            behind: 0,
            modifiedCount: 0,
            untrackedCount: 0,
            isDirty: false,
            healthAvailable: true,
            healthProbedAt: nil,
            lastCommitAt: nil,
            lastCommitTs: nil,
            myLastCommitTs: nil,
            probedAt: nil,
            newestPr: nil,
            recentIssues: [issue],
            recentPrs: [pr],
            recentActivity: [],
            clones: nil,
            clonesDirtyCount: nil,
            anyCloneDirty: nil
        )

        let modified = card.with(position: 2)
        XCTAssertEqual(modified.position, 2)
        XCTAssertEqual(modified.issues, [issue])
        XCTAssertEqual(modified.prs, [pr])
        XCTAssertTrue(modified.hasRecentGitHubItems)
    }
}
