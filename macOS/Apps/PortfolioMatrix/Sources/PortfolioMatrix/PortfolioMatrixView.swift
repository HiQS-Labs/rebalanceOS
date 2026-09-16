import SwiftUI

@MainActor
public struct PortfolioMatrixView: View {
    @StateObject private var viewModel: PortfolioMatrixViewModel

    public init(viewModel: PortfolioMatrixViewModel? = nil) {
        _viewModel = StateObject(wrappedValue: viewModel ?? PortfolioMatrixViewModel())
    }

    public var body: some View {
        ZStack(alignment: .bottomTrailing) {
            VStack(spacing: 0) {
                // Window Header Toolbar
                headerToolbar

                // Summary Statistics Bar
                metricsSummaryBar

                Divider().overlay(Color.white.opacity(0.08))

                // Split-Scroll 2D Matrix
                if let matrix = viewModel.matrix {
                    matrixContent(projects: matrix.projects)
                } else if viewModel.isLoading {
                    VStack {
                        Spacer()
                        ProgressView("Loading Portfolio Matrix...")
                            .progressViewStyle(.circular)
                        Spacer()
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    VStack(spacing: 10) {
                        Spacer()
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundColor(.orange)
                        Text(viewModel.errorMessage ?? "Failed to connect to local server (port 8787).")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        Button("Retry") {
                            Task { await viewModel.refresh() }
                        }
                        .buttonStyle(.bordered)
                        Spacer()
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }

                Divider().overlay(Color.white.opacity(0.08))

                // Footer Status
                footerBar
            }

            // Toast overlay
            if let toast = viewModel.toastMessage {
                HStack(spacing: 8) {
                    Circle()
                        .fill(Color.cyan)
                        .frame(width: 6, height: 6)
                    Text(toast)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.black.opacity(0.85))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.cyan.opacity(0.4), lineWidth: 1))
                .cornerRadius(8)
                .shadow(radius: 6)
                .padding(16)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .frame(minWidth: 520, minHeight: 400)
        .background(Theme.darkBackground)
        .task {
            await viewModel.refresh()
        }
        .sheet(isPresented: $viewModel.isNewIssueModalPresented) {
            let repos = (viewModel.matrix?.projects.map { $0.name } ?? [])
            let uniqueRepos = Array(Set(repos)).sorted()
            NewIssueModal(viewModel: viewModel, availableRepos: uniqueRepos)
        }
    }

    // MARK: - Subviews

    private var headerToolbar: some View {
        HStack(spacing: 8) {
            Text("Focus 5")
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(.white)

            HStack(spacing: 4) {
                Circle()
                    .fill(Color.green)
                    .frame(width: 5, height: 5)
                Text("8787")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.green)
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Color.green.opacity(0.12))
            .cornerRadius(4)

            Spacer()

            Text("Portfolio Matrix")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.cyan)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(Color.cyan.opacity(0.15))
                .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.cyan.opacity(0.3), lineWidth: 1))
                .cornerRadius(5)

            Spacer()

            Button(action: {
                Task { await viewModel.refresh() }
            }) {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help("Refresh Matrix")
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.black.opacity(0.3))
    }

    private var metricsSummaryBar: some View {
        let projs = viewModel.matrix?.projects ?? []
        let totalTasks = projs.reduce(0) { $0 + $1.tasks.count }
        let maxScore = projs.map { $0.computed_score }.max() ?? 0

        return HStack(spacing: 16) {
            HStack(spacing: 4) {
                Text("\(projs.count)")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundColor(.white)
                Text("Projects")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 4) {
                Text("\(totalTasks)")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundColor(.cyan)
                Text("Open Front Tasks")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 4) {
                Text("\(maxScore)")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundColor(.green)
                Text("Max Score")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.black.opacity(0.15))
    }

    private func matrixContent(projects: [MatrixProject]) -> some View {
        HStack(spacing: 0) {
            // Frozen Left Identity Column (130pt)
            VStack(spacing: 0) {
                // Column Header
                HStack {
                    Text("PROJECT")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("SCORE")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 8)
                .frame(height: 28)
                .background(Color.black.opacity(0.4))

                Divider().overlay(Color.white.opacity(0.06))

                // Rows
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        ForEach(Array(projects.enumerated()), id: \.element.id) { index, project in
                            frozenProjectCell(project: project, isEven: index % 2 == 0)
                            Divider().overlay(Color.white.opacity(0.04))
                        }
                    }
                }
            }
            .frame(width: Theme.frozenColumnWidth)
            .background(Color.black.opacity(0.2))

            Divider().overlay(Color.white.opacity(0.12))

            // Horizontally Scrollable Tasks Area
            ScrollView([.horizontal, .vertical]) {
                VStack(spacing: 0) {
                    // Columns Header
                    HStack(spacing: 12) {
                        taskColumnHeader("Task 1 · Immediate Front", color: .cyan)
                        taskColumnHeader("Task 2 · Next Up", color: .blue)
                        taskColumnHeader("Task 3 · Follow-Up", color: .gray)
                    }
                    .padding(.horizontal, 10)
                    .frame(height: 28)
                    .background(Color.black.opacity(0.4))

                    Divider().overlay(Color.white.opacity(0.06))

                    // Task Rows
                    ForEach(Array(projects.enumerated()), id: \.element.id) { index, project in
                        HStack(spacing: 12) {
                            taskCell(task: project.tasks.indices.contains(0) ? project.tasks[0] : nil, project: project)
                            taskCell(task: project.tasks.indices.contains(1) ? project.tasks[1] : nil, project: project)
                            taskCell(task: project.tasks.indices.contains(2) ? project.tasks[2] : nil, project: project)
                        }
                        .padding(.horizontal, 10)
                        .frame(height: Theme.rowHeight)
                        .background(index % 2 == 0 ? Color.white.opacity(0.02) : Color.clear)

                        Divider().overlay(Color.white.opacity(0.04))
                    }
                }
            }
        }
    }

    private func frozenProjectCell(project: MatrixProject, isEven: Bool) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 4) {
                Text(project.name)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white)
                    .lineLimit(1)
                    .help(project.name)

                // Inline + Button
                Button(action: {
                    viewModel.openNewIssueModal(for: project.name)
                }) {
                    Text("＋")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(.secondary)
                        .frame(width: 14, height: 14)
                        .background(Color.white.opacity(0.08))
                        .cornerRadius(3)
                }
                .buttonStyle(.plain)
                .help("Add task to \(project.name)")

                Spacer()

                // Score badge
                Text("\(project.computed_score)")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundColor(scoreColor(project.computed_score))
                    .padding(.horizontal, 4)
                    .padding(.vertical, 1)
                    .background(scoreColor(project.computed_score).opacity(0.15))
                    .cornerRadius(3)
            }

            HStack {
                if let sub = project.subproject, !sub.isEmpty {
                    Text(sub)
                        .font(.system(size: 9))
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                } else {
                    Text("Main")
                        .font(.system(size: 9))
                        .foregroundColor(.secondary.opacity(0.6))
                }
                Spacer()
                Text("R\(project.revenue_ranking)·P\(project.revenue_potential)")
                    .font(.system(size: 8, design: .monospaced))
                    .foregroundColor(.secondary.opacity(0.6))
            }
        }
        .padding(.horizontal, 8)
        .frame(height: Theme.rowHeight)
        .background(isEven ? Color.white.opacity(0.02) : Color.clear)
    }

    private func taskColumnHeader(_ title: String, color: Color) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 5, height: 5)
            Text(title)
                .font(.system(size: 9, weight: .semibold))
                .foregroundColor(.secondary)
            Spacer()
        }
        .frame(width: Theme.taskCardMinWidth)
    }

    private func taskCell(task: MatrixTask?, project: MatrixProject) -> some View {
        Group {
            if let task = task {
                HStack(alignment: .top, spacing: 6) {
                    Button(action: {
                        Task {
                            await viewModel.completeTask(task, in: project)
                        }
                    }) {
                        Image(systemName: "square")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                    .disabled(viewModel.isMutatingTask)

                    Text(task.title)
                        .font(.system(size: 10))
                        .foregroundColor(.white.opacity(0.9))
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)

                    Spacer(minLength: 0)
                }
                .padding(6)
                .frame(width: Theme.taskCardMinWidth, height: Theme.rowHeight - 12)
                .background(Theme.cardBackground)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.cardBorder, lineWidth: 1))
                .cornerRadius(6)
            } else {
                HStack {
                    Text("—")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary.opacity(0.3))
                }
                .frame(width: Theme.taskCardMinWidth, height: Theme.rowHeight - 12)
                .background(Color.white.opacity(0.01))
                .cornerRadius(6)
            }
        }
    }

    private func scoreColor(_ score: Int) -> Color {
        if score >= 8 { return .green }
        if score >= 6 { return .cyan }
        if score >= 4 { return .blue }
        return .orange
    }

    private var footerBar: some View {
        HStack {
            HStack(spacing: 4) {
                Circle().fill(Color.green).frame(width: 4, height: 4)
                Text("Single Writer: POST /api/focus5/goals/complete")
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundColor(.secondary)
            }
            Spacer()
            Text("Frozen: 130pt · Height: 58pt")
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(.secondary.opacity(0.7))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(Color.black.opacity(0.4))
    }
}
