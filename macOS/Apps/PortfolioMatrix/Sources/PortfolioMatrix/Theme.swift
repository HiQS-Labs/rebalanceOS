import SwiftUI

public enum Theme {
    public static let rowHeight: CGFloat = 58.0
    public static let frozenColumnWidth: CGFloat = 130.0
    public static let taskCardMinWidth: CGFloat = 150.0

    public static let darkBackground = Color(red: 11/255, green: 15/255, blue: 23/255)
    public static let panelBackground = Color(red: 22/255, green: 27/255, blue: 34/255).opacity(0.88)
    public static let cellDark = Color(red: 15/255, green: 23/255, blue: 42/255).opacity(0.5)
    public static let cellLight = Color(red: 15/255, green: 23/255, blue: 42/255).opacity(0.3)
    public static let cardBackground = Color(red: 30/255, green: 41/255, blue: 59/255).opacity(0.65)
    public static let cardBorder = Color.white.opacity(0.09)
}
