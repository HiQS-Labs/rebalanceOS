import Foundation
import AppKit
import os

private let ideLog = Logger(subsystem: "me.neochro.Focus5Float", category: "ide-launcher")

/// Dispatches repo opening to the matching IDE based on the prompt's source token.
/// - `claude-code` (or unknown) -> VS Code via VSCodeLauncher
/// - `codex` -> ChatGPT.app (`com.openai.codex`, newer Codex app, not classic)
/// - `agy` -> Antigravity.app (`com.google.antigravity`)
/// - `zcode` -> ZCode.app (`dev.zcode.app`)
enum IDELauncher {
    /// Pure mapping function for bundle ID resolution.
    static func targetBundleID(for ide: String?) -> String {
        guard let raw = ide?.lowercased().trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return "com.microsoft.VSCode"
        }
        if raw.contains("codex") {
            return "com.openai.codex"
        } else if raw.contains("agy") || raw.contains("antigravity") {
            return "com.google.antigravity"
        } else if raw.contains("zcode") {
            return "dev.zcode.app"
        } else {
            return "com.microsoft.VSCode"
        }
    }

    /// Launches the target IDE with the given `repoPath`.
    static func launch(ide: String?, repoPath: String, fallbackURL: String) {
        let bundleID = targetBundleID(for: ide)
        if bundleID == "com.microsoft.VSCode" {
            VSCodeLauncher.launch(repoPath: repoPath, fallbackURL: fallbackURL)
            return
        }

        let appURL = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID)
            ?? fallbackAppURL(for: bundleID)

        guard let targetURL = appURL else {
            ideLog.info("Application for \(bundleID, privacy: .public) not found, falling back to VS Code")
            VSCodeLauncher.launch(repoPath: repoPath, fallbackURL: fallbackURL)
            return
        }

        let conf = NSWorkspace.OpenConfiguration()
        conf.activates = true
        let repoFolderURL = URL(fileURLWithPath: repoPath)

        NSWorkspace.shared.open([repoFolderURL], withApplicationAt: targetURL, configuration: conf) { _, error in
            if let error {
                ideLog.warning("Opening \(repoPath, privacy: .public) in \(bundleID, privacy: .public) failed: \(error.localizedDescription, privacy: .public), activating app directly")
                NSWorkspace.shared.openApplication(at: targetURL, configuration: conf, completionHandler: nil)
            } else {
                ideLog.info("Opened \(repoPath, privacy: .public) in \(bundleID, privacy: .public)")
            }
        }
    }

    private static func fallbackAppURL(for bundleID: String) -> URL? {
        let path: String
        switch bundleID {
        case "com.openai.codex": path = "/Applications/ChatGPT.app"
        case "com.google.antigravity": path = "/Applications/Antigravity.app"
        case "dev.zcode.app": path = "/Applications/ZCode.app"
        default: return nil
        }
        return FileManager.default.fileExists(atPath: path) ? URL(fileURLWithPath: path) : nil
    }
}
