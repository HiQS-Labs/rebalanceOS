import Foundation
import Testing
@testable import TextReplacementCore

@Test
func applePlistCodecRoundTripsItems() throws {
    let codec = ApplePlistCodec()
    let items = [
        AppleTextReplacementItem(phrase: "On my way!", shortcut: "omw"),
        AppleTextReplacementItem(phrase: "Ada Lovelace\nExample Co", shortcut: ";sig")
    ]

    let data = try codec.encode(items)
    let decoded = try codec.decode(data)

    #expect(decoded == items)
}
