import XCTest
@testable import Focus5Float

/// GH-120 — persistence of the roster tiling preference.
///
/// Tiling defaults ON, which makes the absent-key case the interesting one:
/// `UserDefaults.bool(forKey:)` returns false for a key that was never set, so
/// reading the flag that way would silently ship every first run with tiling
/// off — the opposite of the default. These pin the three-state read
/// (never set / set true / set false).
@MainActor
final class RosterLayoutPreferenceTests: XCTestCase {

    private let key = "tileCards"

    override func setUp() {
        super.setUp()
        UserDefaults.standard.removeObject(forKey: key)
    }

    override func tearDown() {
        UserDefaults.standard.removeObject(forKey: key)
        super.tearDown()
    }

    func testAFirstRunTiles() {
        XCTAssertTrue(Focus5Model().tileCards,
                      "Absent key must read as tiled — bool(forKey:) would give false here.")
    }

    func testTurningItOffPersistsAcrossRelaunch() {
        let model = Focus5Model()
        model.tileCards = false
        XCTAssertFalse(Focus5Model().tileCards,
                       "An operator who stacked the roster got re-tiled on relaunch.")
    }

    func testTurningItBackOnPersistsToo() {
        let model = Focus5Model()
        model.tileCards = false
        model.tileCards = true
        XCTAssertTrue(Focus5Model().tileCards)
    }

    func testTheStoredKeyIsTheOneTheModelReads() {
        let model = Focus5Model()
        model.tileCards = false
        XCTAssertEqual(UserDefaults.standard.object(forKey: key) as? Bool, false)
    }
}
