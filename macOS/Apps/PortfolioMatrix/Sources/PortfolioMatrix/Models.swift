import Foundation

public struct PortfolioMatrixResponse: Codable, Equatable {
    public let computed_at: String?
    public let goals_revision: String?
    public let projects: [MatrixProject]

    public init(computed_at: String? = nil, goals_revision: String? = nil, projects: [MatrixProject] = []) {
        self.computed_at = computed_at
        self.goals_revision = goals_revision
        self.projects = projects
    }
}

public struct MatrixProject: Codable, Identifiable, Equatable {
    public let id: String
    public let name: String
    public let subproject: String?
    public let revenue_ranking: Int
    public let revenue_potential: Int
    public let computed_score: Int
    public let tasks: [MatrixTask]

    public init(
        id: String,
        name: String,
        subproject: String? = nil,
        revenue_ranking: Int = 0,
        revenue_potential: Int = 0,
        computed_score: Int = 0,
        tasks: [MatrixTask] = []
    ) {
        self.id = id
        self.name = name
        self.subproject = subproject
        self.revenue_ranking = revenue_ranking
        self.revenue_potential = revenue_potential
        self.computed_score = computed_score
        self.tasks = tasks
    }
}

public struct MatrixTask: Codable, Identifiable, Equatable {
    public let id: String
    public let title: String
    public let line_index: Int
    public let is_blocked: Bool
    public let source_header: String?

    public init(
        id: String,
        title: String,
        line_index: Int,
        is_blocked: Bool = false,
        source_header: String? = nil
    ) {
        self.id = id
        self.title = title
        self.line_index = line_index
        self.is_blocked = is_blocked
        self.source_header = source_header
    }
}

public struct GoalCompleteRequest: Codable {
    public let title: String
    public let line_index: Int?
    public let goals_revision: String?

    public init(title: String, line_index: Int? = nil, goals_revision: String? = nil) {
        self.title = title
        self.line_index = line_index
        self.goals_revision = goals_revision
    }
}

public struct GoalCompleteResponse: Codable {
    public let ok: Bool?
    public let title: String?
    public let line_index: Int?
    public let goals_revision: String?
    public let error: String?
    public let message: String?

    public init(
        ok: Bool? = nil,
        title: String? = nil,
        line_index: Int? = nil,
        goals_revision: String? = nil,
        error: String? = nil,
        message: String? = nil
    ) {
        self.ok = ok
        self.title = title
        self.line_index = line_index
        self.goals_revision = goals_revision
        self.error = error
        self.message = message
    }
}
