import Foundation

// Wire models for GET /focus-5.json — frozen in macOS/Apps/Focus5Float/CONTRACT.md.
// Decode with JSONDecoder().keyDecodingStrategy = .convertFromSnakeCase (see
// SampleData / Focus5Client). Optionals reflect fields that are legitimately
// absent/null in real payloads (no PR, no upstream, non-GitHub/local-only repo,
// empty DB). Unknown wire keys (device_id, head_reflog_ts, index_mtime_ts) are
// intentionally not modeled — Codable ignores them.

struct Focus5Response: Codable {
    let roster: [RepoCard]
    let offRosterWarnings: [OffRosterWarning]
    // GH-105: single most-recently-touched dirty off-roster repo, or nil — a
    // slim "BTW, this went dirty" nudge. Server-computed (pick_newest_dirty_
    // off_roster in focus5_scan.py); already nil on a Dirty Five rerank
    // (?view=dirty), so no client-side view check is needed.
    let dirtyBanner: OffRosterWarning?
    let computedAt: String?          // ISO-8601; nil when roster empty
    let rankingMode: String?         // "recent_activity" | "dirty_first" | nil
    let summary: Summary

    struct Summary: Codable {
        let discovered: Int
        let rosterSize: Int
        let offRosterAttention: Int
    }
}

struct RepoCard: Codable, Identifiable {
    var id: String { localPath }     // stable per machine

    let position: Int
    let repoName: String
    let repoFullName: String?        // nil for non-GitHub / local-only
    let localPath: String            // LOCAL-ONLY
    let remoteUrl: String?           // SENSITIVE
    let vscodeUrl: String            // LOCAL-ONLY
    let rankReason: String
    let rankingMode: String
    let computedAt: String

    // Tree health (live re-probe folded over the cached signals)
    let branch: String?
    let upstream: String?
    let hasUpstream: Bool?
    let ahead: Int
    let behind: Int
    let modifiedCount: Int
    let untrackedCount: Int
    let isDirty: Bool
    let healthAvailable: Bool
    let healthProbedAt: String?

    // Activity timestamps (any may be nil)
    let lastCommitAt: String?
    let lastCommitTs: Int?
    let myLastCommitTs: Int?
    let probedAt: String?

    let newestPr: NewestPR?
    let recentIssues: [GitHubItemRef]?
    let recentPrs: [GitHubItemRef]?
    let recentActivity: [Commit]

    // Active full clones (GH-204)
    let clones: [RepoClone]?
    let clonesDirtyCount: Int?
    let anyCloneDirty: Bool?

    var activeClones: [RepoClone] { clones ?? [] }
    var hasClones: Bool { !activeClones.isEmpty }
    var isAnyCloneDirty: Bool { anyCloneDirty ?? activeClones.contains { $0.isDirty } }
    var issues: [GitHubItemRef] { recentIssues ?? [] }
    var prs: [GitHubItemRef] { recentPrs ?? [] }
    var hasRecentGitHubItems: Bool { !issues.isEmpty || !prs.isEmpty }

    init(
        position: Int,
        repoName: String,
        repoFullName: String?,
        localPath: String,
        remoteUrl: String?,
        vscodeUrl: String,
        rankReason: String,
        rankingMode: String,
        computedAt: String,
        branch: String?,
        upstream: String?,
        hasUpstream: Bool?,
        ahead: Int,
        behind: Int,
        modifiedCount: Int,
        untrackedCount: Int,
        isDirty: Bool,
        healthAvailable: Bool,
        healthProbedAt: String?,
        lastCommitAt: String?,
        lastCommitTs: Int?,
        myLastCommitTs: Int?,
        probedAt: String?,
        newestPr: NewestPR?,
        recentIssues: [GitHubItemRef]? = nil,
        recentPrs: [GitHubItemRef]? = nil,
        recentActivity: [Commit],
        clones: [RepoClone]?,
        clonesDirtyCount: Int?,
        anyCloneDirty: Bool?
    ) {
        self.position = position
        self.repoName = repoName
        self.repoFullName = repoFullName
        self.localPath = localPath
        self.remoteUrl = remoteUrl
        self.vscodeUrl = vscodeUrl
        self.rankReason = rankReason
        self.rankingMode = rankingMode
        self.computedAt = computedAt
        self.branch = branch
        self.upstream = upstream
        self.hasUpstream = hasUpstream
        self.ahead = ahead
        self.behind = behind
        self.modifiedCount = modifiedCount
        self.untrackedCount = untrackedCount
        self.isDirty = isDirty
        self.healthAvailable = healthAvailable
        self.healthProbedAt = healthProbedAt
        self.lastCommitAt = lastCommitAt
        self.lastCommitTs = lastCommitTs
        self.myLastCommitTs = myLastCommitTs
        self.probedAt = probedAt
        self.newestPr = newestPr
        self.recentIssues = recentIssues
        self.recentPrs = recentPrs
        self.recentActivity = recentActivity
        self.clones = clones
        self.clonesDirtyCount = clonesDirtyCount
        self.anyCloneDirty = anyCloneDirty
    }

    func with(
        position: Int? = nil,
        clones: [RepoClone]? = nil,
        clonesDirtyCount: Int? = nil,
        anyCloneDirty: Bool? = nil,
        recentIssues: [GitHubItemRef]? = nil,
        recentPrs: [GitHubItemRef]? = nil
    ) -> RepoCard {
        RepoCard(
            position: position ?? self.position,
            repoName: self.repoName,
            repoFullName: self.repoFullName,
            localPath: self.localPath,
            remoteUrl: self.remoteUrl,
            vscodeUrl: self.vscodeUrl,
            rankReason: self.rankReason,
            rankingMode: self.rankingMode,
            computedAt: self.computedAt,
            branch: self.branch,
            upstream: self.upstream,
            hasUpstream: self.hasUpstream,
            ahead: self.ahead,
            behind: self.behind,
            modifiedCount: self.modifiedCount,
            untrackedCount: self.untrackedCount,
            isDirty: self.isDirty,
            healthAvailable: self.healthAvailable,
            healthProbedAt: self.healthProbedAt,
            lastCommitAt: self.lastCommitAt,
            lastCommitTs: self.lastCommitTs,
            myLastCommitTs: self.myLastCommitTs,
            probedAt: self.probedAt,
            newestPr: self.newestPr,
            recentIssues: recentIssues ?? self.recentIssues,
            recentPrs: recentPrs ?? self.recentPrs,
            recentActivity: self.recentActivity,
            clones: clones ?? self.clones,
            clonesDirtyCount: clonesDirtyCount ?? self.clonesDirtyCount,
            anyCloneDirty: anyCloneDirty ?? self.anyCloneDirty
        )
    }

    func asClone() -> RepoClone {
        RepoClone(
            repoName: repoName,
            localPath: localPath,
            branch: branch,
            ahead: ahead,
            behind: behind,
            modifiedCount: modifiedCount,
            untrackedCount: untrackedCount,
            isDirty: isDirty,
            lastCommitAt: lastCommitAt,
            myLastCommitTs: myLastCommitTs,
            vscodeUrl: vscodeUrl
        )
    }
}

struct RepoClone: Codable, Identifiable, Equatable {
    var id: String { localPath }

    let repoName: String
    let localPath: String            // LOCAL-ONLY
    let branch: String?
    let ahead: Int
    let behind: Int
    let modifiedCount: Int
    let untrackedCount: Int
    let isDirty: Bool
    let lastCommitAt: String?
    let myLastCommitTs: Int?
    let vscodeUrl: String            // LOCAL-ONLY
}

struct NewestPR: Codable {
    let number: Int
    let title: String
    let state: String                // "open" | "closed" | "merged"
    let htmlUrl: String
    let isDraft: Bool
    let isMerged: Bool
}

struct GitHubItemRef: Codable, Identifiable, Equatable {
    var id: Int { number }
    let number: Int
    let htmlUrl: String
    let title: String?
}

struct Commit: Codable, Identifiable {
    var id: String { sha }
    let sha: String
    let subject: String
    let committedAt: String          // ISO-8601
    let authorEmail: String          // SENSITIVE (PII) — never re-export
}

struct OffRosterWarning: Codable, Identifiable {
    var id: String { localPath }
    let repoName: String
    let localPath: String            // LOCAL-ONLY
    let repoFullName: String?
    let branch: String?
    let ahead: Int
    let modifiedCount: Int
    let untrackedCount: Int
    let isDirty: Bool
    let probedAt: String?
    // GH-105: last local commit before this repo went dirty (epoch seconds) —
    // was already on the wire for every off-roster row (GH-81) but unmodeled
    // here; needed now to render "last commit Xh ago" on the dirty banner.
    let myLocalCommitTs: Int?
    // GH-104: server-computed off-roster reason ("uncommitted changes",
    // "N ahead of origin", fallback) from focus5_scan.off_roster_reason().
    let warningReason: String?

    func asClone() -> RepoClone {
        let vscode = "vscode://file\(localPath.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? localPath)"
        return RepoClone(
            repoName: repoName,
            localPath: localPath,
            branch: branch,
            ahead: ahead,
            behind: 0,
            modifiedCount: modifiedCount,
            untrackedCount: untrackedCount,
            isDirty: isDirty,
            lastCommitAt: nil,
            myLastCommitTs: myLocalCommitTs,
            vscodeUrl: vscode
        )
    }
}

struct Focus5GoalsResponse: Codable {
    let exists: Bool
    let items: [ObsidianReminder]
    let path: String?
    let totalOpen: Int
    let reason: String?
    let message: String?
}

struct Focus5GoalCompleteResponse: Codable {
    let ok: Bool
    let title: String
    let lineIndex: Int
    let exists: Bool
    let items: [ObsidianReminder]
    let path: String?
    let totalOpen: Int
    let reason: String?
    let message: String?
}

struct ObsidianReminder: Codable, Identifiable {
    var id: Int { lineIndex }
    let title: String
    let description: String
    let lineIndex: Int
}
