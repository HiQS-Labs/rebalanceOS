import Foundation

public enum ClientError: LocalizedError, Equatable {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, message: String)
    case staleRevision
    case ambiguousGoal(String)
    case transportError(String)
    case allCandidatesFailed(String)

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
        case .allCandidatesFailed(let msg):
            return "Could not connect to local server: \(msg)"
        }
    }
}

public final class PortfolioClient: @unchecked Sendable {
    public let defaultBaseURL: URL
    public static let pulseServerBaseURL = URL(string: "http://127.0.0.1:8767")!
    public static let devServerBaseURL = URL(string: "http://127.0.0.1:8787")!

    private let lock = NSLock()
    private var _activeBaseURL: URL?

    public init(baseURL: URL = PortfolioClient.devServerBaseURL) {
        self.defaultBaseURL = baseURL
    }

    public var activeBaseURL: URL? {
        lock.lock()
        defer { lock.unlock() }
        return _activeBaseURL
    }

    public var activePort: Int? {
        activeBaseURL?.port
    }

    public func setActiveBaseURL(_ url: URL?) {
        lock.lock()
        defer { lock.unlock() }
        _activeBaseURL = url
    }

    public var candidateBaseURLs: [URL] {
        let env = ProcessInfo.processInfo.environment
        if let raw = env["PORTFOLIO_MATRIX_BASE_URL"] ?? env["FOCUS5_BASE_URL"],
           let override = URL(string: raw) {
            return [override]
        }
        var candidates: [URL] = [defaultBaseURL]
        if defaultBaseURL != Self.pulseServerBaseURL {
            candidates.append(Self.pulseServerBaseURL)
        }
        return candidates
    }

    public func fetchMatrix() async throws -> PortfolioMatrixResponse {
        var attempts: [String] = []

        var candidates = candidateBaseURLs
        if let current = activeBaseURL, let idx = candidates.firstIndex(of: current), idx > 0 {
            candidates.remove(at: idx)
            candidates.insert(current, at: 0)
        }

        for base in candidates {
            let url = base.appendingPathComponent("portfolio-matrix.json")
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.timeoutInterval = 4.0

            do {
                let (data, response) = try await URLSession.shared.data(for: request)
                guard let http = response as? HTTPURLResponse else {
                    attempts.append("\(base.port ?? 80): invalid response")
                    continue
                }
                guard http.statusCode == 200 else {
                    attempts.append("\(base.port ?? 80): HTTP \(http.statusCode)")
                    continue
                }
                let decoder = JSONDecoder()
                let matrix = try decoder.decode(PortfolioMatrixResponse.self, from: data)
                setActiveBaseURL(base)
                return matrix
            } catch let err as DecodingError {
                attempts.append("\(base.port ?? 80): decode error (\(err.localizedDescription))")
            } catch {
                attempts.append("\(base.port ?? 80): \(error.localizedDescription)")
            }
        }

        setActiveBaseURL(nil)
        throw ClientError.allCandidatesFailed(attempts.joined(separator: "; "))
    }

    public func completeTask(
        title: String,
        lineIndex: Int?,
        revision: String?
    ) async throws -> GoalCompleteResponse {
        let targetBase = activeBaseURL ?? candidateBaseURLs.first!
        let url = targetBase.appendingPathComponent("api/focus5/goals/complete")
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
