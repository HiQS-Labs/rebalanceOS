import XCTest
@testable import PortfolioMatrix

final class MatrixTests: XCTestCase {
    func testDecodeMatrixResponse() throws {
        let json = """
        {
            "computed_at": "2026-09-15T18:00:00Z",
            "goals_revision": "abcdef123456",
            "projects": [
                {
                    "id": "Inspired Magazine:Monetization",
                    "name": "Inspired Magazine",
                    "subproject": "Monetization",
                    "revenue_ranking": 5,
                    "revenue_potential": 4,
                    "computed_score": 9,
                    "tasks": [
                        {
                            "id": "Inspired Magazine:Monetization:1",
                            "title": "Setup Stripe Connect",
                            "line_index": 1,
                            "is_blocked": false,
                            "source_header": "Inspired Magazine / Monetization"
                        }
                    ]
                }
            ]
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(PortfolioMatrixResponse.self, from: json)
        XCTAssertEqual(decoded.goals_revision, "abcdef123456")
        XCTAssertEqual(decoded.projects.count, 1)

        let project = decoded.projects[0]
        XCTAssertEqual(project.id, "Inspired Magazine:Monetization")
        XCTAssertEqual(project.name, "Inspired Magazine")
        XCTAssertEqual(project.subproject, "Monetization")
        XCTAssertEqual(project.computed_score, 9)
        XCTAssertEqual(project.tasks.count, 1)

        let task = project.tasks[0]
        XCTAssertEqual(task.title, "Setup Stripe Connect")
        XCTAssertEqual(task.line_index, 1)
        XCTAssertFalse(task.is_blocked)
    }

    func testGoalCompleteRequestEncoding() throws {
        let req = GoalCompleteRequest(title: "Test Task", line_index: 5, goals_revision: "rev123")
        let data = try JSONEncoder().encode(req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

        XCTAssertEqual(json?["title"] as? String, "Test Task")
        XCTAssertEqual(json?["line_index"] as? Int, 5)
        XCTAssertEqual(json?["goals_revision"] as? String, "rev123")
    }

    func testGoalCompleteResponseDecoding() throws {
        let successJson = """
        {
            "ok": true,
            "title": "Test Task",
            "line_index": 5,
            "goals_revision": "rev456"
        }
        """.data(using: .utf8)!

        let success = try JSONDecoder().decode(GoalCompleteResponse.self, from: successJson)
        XCTAssertTrue(success.ok ?? false)
        XCTAssertEqual(success.title, "Test Task")
        XCTAssertEqual(success.goals_revision, "rev456")

        let errorJson = """
        {
            "ok": false,
            "error": "stale_goal_snapshot",
            "message": "Goal file has changed"
        }
        """.data(using: .utf8)!

        let errorResp = try JSONDecoder().decode(GoalCompleteResponse.self, from: errorJson)
        XCTAssertFalse(errorResp.ok ?? true)
        XCTAssertEqual(errorResp.error, "stale_goal_snapshot")
    }

    func testPortfolioClientCandidateBaseURLs() throws {
        let client = PortfolioClient()
        let urls = client.candidateBaseURLs
        XCTAssertEqual(urls.count, 2)
        XCTAssertEqual(urls[0], URL(string: "http://127.0.0.1:8787")!)
        XCTAssertEqual(urls[1], URL(string: "http://127.0.0.1:8767")!)
    }

    func testClientErrorDescriptions() throws {
        let err = ClientError.allCandidatesFailed("8787: offline, 8767: 404")
        XCTAssertEqual(err.errorDescription, "Could not connect to local server: 8787: offline, 8767: 404")
    }
}
