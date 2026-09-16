import Foundation

public enum ClientError: LocalizedError, Equatable {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, message: String)
    case staleRevision
    case ambiguousGoal(String)
    case transportError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let code, let msg):
            return "HTTP \(code): \(msg)"
        case .staleRevision:
            return "Task state changed on server. Refreshing..."
        case .ambiguousGoal(let title):
            return "Multiple goals match '\(title)'."
        case .transportError(let msg):
            return "Network error: \(msg)"
        }
    }
}

public final class PortfolioClient: Sendable {
    public let baseURL: URL

    public init(baseURL: URL = URL(string: "http://127.0.0.1:8787")!) {
        self.baseURL = baseURL
    }

    public func fetchMatrix() async throws -> PortfolioMatrixResponse {
        let url = baseURL.appendingPathComponent("portfolio-matrix.json")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 5.0

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw ClientError.invalidResponse
            }
            guard http.statusCode == 200 else {
                throw ClientError.httpError(statusCode: http.statusCode, message: "Failed to fetch matrix")
            }
            let decoder = JSONDecoder()
            return try decoder.decode(PortfolioMatrixResponse.self, from: data)
        } catch let err as ClientError {
            throw err
        } catch {
            throw ClientError.transportError(error.localizedDescription)
        }
    }

    public func completeTask(
        title: String,
        lineIndex: Int?,
        revision: String?
    ) async throws -> GoalCompleteResponse {
        let url = baseURL.appendingPathComponent("api/focus5/goals/complete")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 5.0

        let body = GoalCompleteRequest(title: title, line_index: lineIndex, goals_revision: revision)
        request.httpBody = try JSONEncoder().encode(body)

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw ClientError.invalidResponse
            }

            if http.statusCode == 409 {
                if let decoded = try? JSONDecoder().decode(GoalCompleteResponse.self, from: data) {
                    if decoded.error == "stale_goal_snapshot" {
                        throw ClientError.staleRevision
                    } else if decoded.error == "ambiguous_goal_title" {
                        throw ClientError.ambiguousGoal(title)
                    }
                }
                throw ClientError.httpError(statusCode: 409, message: "Conflict")
            }

            guard http.statusCode == 200 else {
                throw ClientError.httpError(statusCode: http.statusCode, message: "Completion failed")
            }

            let decoder = JSONDecoder()
            return try decoder.decode(GoalCompleteResponse.self, from: data)
        } catch let err as ClientError {
            throw err
        } catch {
            throw ClientError.transportError(error.localizedDescription)
        }
    }
}
