import Foundation

/// One parsed entry from the CLIO-rendered prompt log Markdown export.
/// `id` is repo+timestamp — stable across re-reads of the same file since CLIO
/// never rewrites an entry once emitted, which is also what makes pinning by
/// `id` survive a refresh.
struct PromptLogEntry: Identifiable, Equatable {
    let repo: String
    let timestamp: String      // raw ISO-8601, e.g. "2026-07-09T18:42:11Z"
    let machine: String
    let branch: String?
    let ide: String?
    let prompt: String

    init(repo: String, timestamp: String, machine: String, branch: String? = nil, ide: String? = nil, prompt: String) {
        self.repo = repo
        self.timestamp = timestamp
        self.machine = machine
        self.branch = branch
        self.ide = ide
        self.prompt = prompt
    }

    var id: String { "\(repo)|\(timestamp)" }

    /// First 200 characters of `prompt` — enough to recognize the entry at a
    /// glance without re-reading the whole thing.
    var truncatedPrompt: String {
        if prompt.count <= 200 { return prompt }
        return String(prompt.prefix(200)) + "…"
    }
}
