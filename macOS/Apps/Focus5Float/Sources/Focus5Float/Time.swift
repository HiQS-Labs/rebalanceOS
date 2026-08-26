import Foundation

// Relative-time + staleness helpers (the Swift analogue of the web `_ago`).
// Parses the ISO-8601 strings the contract carries (computed_at, committed_at).
enum RelTime {
    /// "just now" / "5m ago" / "3h ago" / "2d ago"; "" for nil.
    static func ago(_ date: Date?, now: Date = Date()) -> String {
        guard let date else { return "" }
        let s = max(0, now.timeIntervalSince(date))
        switch s {
        case ..<60:    return "just now"
        case ..<3600:  return "\(Int(s / 60))m ago"
        case ..<86400: return "\(Int(s / 3600))h ago"
        default:       return "\(Int(s / 86400))d ago"
        }
    }

    /// Same, from an ISO-8601 string; "" for nil/unparseable.
    static func ago(_ iso: String?, now: Date = Date()) -> String {
        guard let iso, let date = parse(iso) else { return "" }
        return ago(date, now: now)
    }

    static func isOlderThan(_ iso: String?, hours: Double, now: Date = Date()) -> Bool {
        guard let iso, let date = parse(iso) else { return false }
        return now.timeIntervalSince(date) > hours * 3600
    }

    /// Parses the timestamp shapes this app is actually fed.
    ///
    /// The Focus 5 contract carries ISO-8601 (`computed_at`, `committed_at`).
    /// CLIO's prompt log does NOT: on 2026-08-21 it switched from
    /// `2026-08-21T15:48:18Z` to local wall-clock plus a zone abbreviation,
    /// `2026-08-24 19:57:39 PDT`. `ISO8601DateFormatter` rejects that outright,
    /// so every prompt written since renders a BLANK relative-time pill — 1,460
    /// of 1,951 entries in the operator's live log at the time of this fix.
    /// Both shapes are parsed, because the log is a mix and the old entries do
    /// not get rewritten.
    static func parse(_ iso: String) -> Date? {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let d = f.date(from: iso) { return d }
        f.formatOptions = [.withInternetDateTime]
        if let d = f.date(from: iso) { return d }
        return parseLocalWallClock(iso)
    }

    /// `2026-08-24 19:57:39 PDT`. POSIX locale so the parse does not shift with
    /// the operator's region, and an explicit `timeZone` fallback because
    /// `DateFormatter` silently fails on a zone abbreviation it does not know —
    /// which would put us straight back to a blank pill.
    private static func parseLocalWallClock(_ raw: String) -> Date? {
        let trimmed = raw.trimmingCharacters(in: .whitespaces)

        let zoned = DateFormatter()
        zoned.locale = Locale(identifier: "en_US_POSIX")
        zoned.dateFormat = "yyyy-MM-dd HH:mm:ss zzz"
        if let d = zoned.date(from: trimmed) { return d }

        // Unknown or absent abbreviation: drop it and read the wall clock in the
        // machine's current zone. Wrong by an hour across a DST boundary for a
        // log written elsewhere, which is still enormously better than showing
        // nothing at all.
        let bare = DateFormatter()
        bare.locale = Locale(identifier: "en_US_POSIX")
        bare.timeZone = .current
        bare.dateFormat = "yyyy-MM-dd HH:mm:ss"
        let withoutZone = trimmed.split(separator: " ").prefix(2).joined(separator: " ")
        return bare.date(from: withoutZone)
    }
}
