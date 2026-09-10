import XCTest
@testable import Focus5Float

final class CloneGroupingTests: XCTestCase {
    func testDecodeRepoCardWithoutClones() throws {
        let json = """
        {
            "position": 1,
            "repo_name": "XYZ-forge",
            "repo_full_name": "Hypercart-Dev-Tools/XYZ-forge",
            "local_path": "/repos/XYZ-forge",
            "remote_url": "https://github.com/Hypercart-Dev-Tools/XYZ-forge.git",
            "vscode_url": "vscode://file/repos/XYZ-forge",
            "rank_reason": "your commit just now",
            "ranking_mode": "recent_activity",
            "computed_at": "2026-09-10T12:00:00Z",
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
        let card = try decoder.decode(RepoCard.self, from: Data(json.utf8))

        XCTAssertNil(card.clones)
        XCTAssertFalse(card.hasClones)
        XCTAssertTrue(card.activeClones.isEmpty)
        XCTAssertFalse(card.isAnyCloneDirty)
    }

    func testDecodeRepoCardWithClones() throws {
        let json = """
        {
            "position": 1,
            "repo_name": "XYZ-forge",
            "repo_full_name": "Hypercart-Dev-Tools/XYZ-forge",
            "local_path": "/repos/XYZ-forge",
            "remote_url": "https://github.com/Hypercart-Dev-Tools/XYZ-forge.git",
            "vscode_url": "vscode://file/repos/XYZ-forge",
            "rank_reason": "your commit 5m ago",
            "ranking_mode": "recent_activity",
            "computed_at": "2026-09-10T12:00:00Z",
            "ahead": 0,
            "behind": 0,
            "modified_count": 0,
            "untracked_count": 0,
            "is_dirty": false,
            "health_available": true,
            "recent_activity": [],
            "clones": [
                {
                    "repo_name": "XYZ-forge-gh365",
                    "local_path": "/repos/XYZ-forge-gh365",
                    "branch": "feat/gh365",
                    "ahead": 1,
                    "behind": 0,
                    "modified_count": 2,
                    "untracked_count": 0,
                    "is_dirty": true,
                    "last_commit_at": "2026-09-10T11:55:00Z",
                    "my_last_commit_ts": 1725969300,
                    "vscode_url": "vscode://file/repos/XYZ-forge-gh365"
                }
            ],
            "clones_dirty_count": 1,
            "any_clone_dirty": true
        }
        """
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let card = try decoder.decode(RepoCard.self, from: Data(json.utf8))

        XCTAssertTrue(card.hasClones)
        XCTAssertEqual(card.activeClones.count, 1)
        XCTAssertTrue(card.isAnyCloneDirty)

        let clone = card.activeClones[0]
        XCTAssertEqual(clone.repoName, "XYZ-forge-gh365")
        XCTAssertEqual(clone.branch, "feat/gh365")
        XCTAssertTrue(clone.isDirty)
        XCTAssertEqual(clone.ahead, 1)
        XCTAssertEqual(clone.modifiedCount, 2)
        XCTAssertEqual(clone.vscodeUrl, "vscode://file/repos/XYZ-forge-gh365")
    }

    private func makeCard(
        position: Int,
        name: String,
        path: String,
        repoFullName: String?,
        branch: String? = "main",
        isDirty: Bool = false
    ) -> RepoCard {
        RepoCard(
            position: position,
            repoName: name,
            repoFullName: repoFullName,
            localPath: path,
            remoteUrl: nil,
            vscodeUrl: "vscode://file\(path)",
            rankReason: "test",
            rankingMode: "recent_activity",
            computedAt: "2026-09-10T12:00:00Z",
            branch: branch,
            upstream: nil,
            hasUpstream: false,
            ahead: 0,
            behind: 0,
            modifiedCount: isDirty ? 1 : 0,
            untrackedCount: 0,
            isDirty: isDirty,
            healthAvailable: true,
            healthProbedAt: nil,
            lastCommitAt: nil,
            lastCommitTs: nil,
            myLastCommitTs: nil,
            probedAt: nil,
            newestPr: nil,
            recentActivity: [],
            clones: nil,
            clonesDirtyCount: nil,
            anyCloneDirty: nil
        )
    }

    func testFoldClonesGroupsChildCheckoutsIntoParent() {
        let cards = [
            makeCard(position: 1, name: "XYZ-forge-gh365", path: "/repos/XYZ-forge-gh365", repoFullName: "Hypercart-Dev-Tools/XYZ-forge", branch: "feat/gh365", isDirty: true),
            makeCard(position: 2, name: "XYZ-forge-qual3", path: "/repos/XYZ-forge-qual3", repoFullName: "Hypercart-Dev-Tools/XYZ-forge", branch: "feat/qual3"),
            makeCard(position: 3, name: "rebalanceOS-gh144", path: "/repos/rebalanceOS-gh144", repoFullName: "HiQS-Labs/rebalanceOS", branch: "feat/gh144"),
            makeCard(position: 4, name: "XYZ-forge-gh384", path: "/repos/XYZ-forge-gh384", repoFullName: "Hypercart-Dev-Tools/XYZ-forge", branch: "feat/gh384"),
            makeCard(position: 5, name: "XYZ-forge", path: "/repos/XYZ-forge", repoFullName: "Hypercart-Dev-Tools/XYZ-forge", branch: "development"),
            makeCard(position: 6, name: "rebalanceOS", path: "/repos/rebalanceOS", repoFullName: "HiQS-Labs/rebalanceOS", branch: "development"),
        ]

        let folded = Focus5Model.foldClones(into: cards)

        XCTAssertEqual(folded.count, 2)

        // First parent is XYZ-forge
        XCTAssertEqual(folded[0].repoName, "XYZ-forge")
        XCTAssertEqual(folded[0].position, 1)
        XCTAssertEqual(folded[0].activeClones.count, 3)
        let cloneNames = Set(folded[0].activeClones.map(\.repoName))
        XCTAssertEqual(cloneNames, ["XYZ-forge-gh365", "XYZ-forge-qual3", "XYZ-forge-gh384"])
        XCTAssertTrue(folded[0].isAnyCloneDirty)

        // Second parent is rebalanceOS
        XCTAssertEqual(folded[1].repoName, "rebalanceOS")
        XCTAssertEqual(folded[1].position, 2)
        XCTAssertEqual(folded[1].activeClones.count, 1)
        XCTAssertEqual(folded[1].activeClones[0].repoName, "rebalanceOS-gh144")
    }
}
