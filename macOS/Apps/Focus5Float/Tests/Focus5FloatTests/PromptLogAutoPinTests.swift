import XCTest
@testable import Focus5Float

/// GH-120 — the Clio viewer's timestamp parsing and automatic "newest per repo"
/// pinning.
@MainActor
final class PromptLogAutoPinTests: XCTestCase {

    // Manual pins persist to UserDefaults, so a model built in one test inherits
    // whatever a previous one pinned. Clear the key around every test or the
    // auto-pin assertions read a neighbour's state.
    private static let pinsDefaultsKey = "pinnedPromptLogIDs"

    override func setUp() {
        super.setUp()
        UserDefaults.standard.removeObject(forKey: Self.pinsDefaultsKey)
    }

    override func tearDown() {
        UserDefaults.standard.removeObject(forKey: Self.pinsDefaultsKey)
        super.tearDown()
    }

    // MARK: Timestamps

    /// CLIO changed timestamp format on 2026-08-21, from ISO-8601 to local
    /// wall-clock plus a zone abbreviation. The app parsed only the former, so
    /// every prompt written after the change showed a BLANK relative-time pill.
    /// Both shapes must parse, because the log is a permanent mix — old entries
    /// are never rewritten.
    func testBothTimestampFormatsInTheLogParse() {
        XCTAssertNotNil(RelTime.parse("2026-08-21T15:48:18Z"),
                        "The pre-2026-08-21 ISO-8601 form stopped parsing.")
        XCTAssertNotNil(RelTime.parse("2026-08-24 19:57:39 PDT"),
                        "The current CLIO form does not parse — the date pill will be blank.")
    }

    func testTheLocalFormatProducesARelativeStringNotAnEmptyOne() {
        let now = RelTime.parse("2026-08-24 21:57:39 PDT")!
        let then = "2026-08-24 19:57:39 PDT"
        XCTAssertEqual(RelTime.ago(then, now: now), "2h ago")
    }

    func testAnUnparseableStampStillYieldsEmptySoTheViewCanHideThePill() {
        XCTAssertEqual(RelTime.ago("not a date", now: Date()), "")
    }

    func testAnUnknownZoneAbbreviationFallsBackRatherThanGivingUp() {
        // A log written on a machine whose zone abbreviation Foundation does not
        // know must still show an age — an hour of skew beats a blank pill.
        XCTAssertNotNil(RelTime.parse("2026-08-24 19:57:39 XYZ"))
    }

    // MARK: Auto-pinning

    private func entry(_ repo: String, _ stamp: String) -> PromptLogEntry {
        PromptLogEntry(repo: repo, timestamp: stamp, machine: "m", branch: "main", prompt: "p-\(repo)-\(stamp)")
    }

    /// Newest-first, which is the order CLIO writes and the reader preserves.
    private func model(_ entries: [PromptLogEntry]) -> Focus5Model {
        let m = Focus5Model()
        m.promptLogEntries = entries
        return m
    }

    func testEachRepoContributesExactlyItsNewestPrompt() {
        let m = model([
            entry("alpha", "2026-08-24 12:00:00 PDT"),
            entry("beta",  "2026-08-24 11:00:00 PDT"),
            entry("alpha", "2026-08-24 10:00:00 PDT"),
            entry("beta",  "2026-08-24 09:00:00 PDT"),
        ])
        let auto = m.autoPinnedPromptLogEntries
        XCTAssertEqual(auto.map(\.repo), ["alpha", "beta"])
        XCTAssertEqual(auto.map(\.timestamp),
                       ["2026-08-24 12:00:00 PDT", "2026-08-24 11:00:00 PDT"],
                       "An older prompt won its repo's slot.")
    }

    func testANewerPromptFromARepoTakesOverThatRepoSlot() {
        // The whole "pinned until there's a newer message from that repo"
        // contract: appending a newer prompt must silently replace the winner,
        // with no eviction step and nothing left stale behind it.
        let m = model([entry("alpha", "2026-08-24 10:00:00 PDT")])
        XCTAssertEqual(m.autoPinnedPromptLogEntries.first?.timestamp, "2026-08-24 10:00:00 PDT")

        m.promptLogEntries.insert(entry("alpha", "2026-08-24 13:00:00 PDT"), at: 0)
        XCTAssertEqual(m.autoPinnedPromptLogEntries.count, 1, "The superseded prompt stayed held up.")
        XCTAssertEqual(m.autoPinnedPromptLogEntries.first?.timestamp, "2026-08-24 13:00:00 PDT")
    }

    func testTheScanOnlyLooksAtTheLastThirtyPrompts() {
        // A repo that has been quiet for more than 30 messages should drop out
        // rather than hold a slot indefinitely.
        var entries = (0..<30).map { entry("busy", "2026-08-24 \(String(format: "%02d", $0 % 24)):00:00 PDT") }
        entries.append(entry("quiet", "2026-08-01 09:00:00 PDT"))
        let m = model(entries)
        XCTAssertEqual(m.autoPinnedPromptLogEntries.map(\.repo), ["busy"])
    }

    func testAManualPinWinsAndTheEntryIsNotShownTwice() {
        let m = model([
            entry("alpha", "2026-08-24 12:00:00 PDT"),
            entry("alpha", "2026-08-24 10:00:00 PDT"),
        ])
        m.togglePin(m.promptLogEntries[0])

        XCTAssertTrue(m.autoPinnedPromptLogEntries.isEmpty,
                      "alpha's newest is manually pinned; it must not also auto-pin.")
        XCTAssertFalse(m.autoPinnedPromptLogEntries.contains { $0.timestamp == "2026-08-24 10:00:00 PDT" },
                       "An older prompt was promoted because the newest was manually pinned.")
    }

    func testAutoPinsDoNotConsumeTheFiveSlotManualQueue() {
        // Five busy repos would otherwise fill the manual queue permanently and
        // the pin button would stop working.
        let m = model((0..<6).map { entry("repo-\($0)", "2026-08-24 1\($0):00:00 PDT") })
        XCTAssertEqual(m.autoPinnedPromptLogEntries.count, 6)
        XCTAssertTrue(m.pinnedPromptLogIDs.isEmpty, "Auto-pinning wrote into the manual pin queue.")

        m.togglePin(m.promptLogEntries[0])
        XCTAssertEqual(m.pinnedPromptLogIDs.count, 1, "The manual pin button stopped working.")
    }

    func testAnAutoPinnedEntryIsNotAlsoInTheMainFeed() {
        let m = model([
            entry("alpha", "2026-08-24 12:00:00 PDT"),
            entry("alpha", "2026-08-24 10:00:00 PDT"),
        ])
        let feed = m.unpinnedPromptLogEntries.map(\.timestamp)
        XCTAssertEqual(feed, ["2026-08-24 10:00:00 PDT"],
                       "The held-up prompt is duplicated in the feed below it.")
    }
}
