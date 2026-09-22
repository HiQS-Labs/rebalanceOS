// swift-tools-version:5.10
import PackageDescription

let package = Package(
    name: "PortfolioMatrix",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "PortfolioMatrix",
            path: "Sources/PortfolioMatrix"
        ),
        .testTarget(
            name: "PortfolioMatrixTests",
            dependencies: ["PortfolioMatrix"],
            path: "Tests/PortfolioMatrixTests"
        ),
    ]
)
