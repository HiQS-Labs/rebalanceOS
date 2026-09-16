import SwiftUI

public struct NewIssueModal: View {
    @ObservedObject var viewModel: PortfolioMatrixViewModel
    let availableRepos: [String]

    @State private var selectedRepo: String
    @State private var title: String = ""
    @State private var prsText: String = ""
    @State private var descriptionText: String = ""

    public init(viewModel: PortfolioMatrixViewModel, availableRepos: [String]) {
        self.viewModel = viewModel
        self.availableRepos = availableRepos
        _selectedRepo = State(initialValue: viewModel.selectedRepoForNewIssue.isEmpty ? (availableRepos.first ?? "") : viewModel.selectedRepoForNewIssue)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header
            HStack {
                Image(systemName: "plus.square.fill")
                    .foregroundColor(.cyan)
                    .font(.title3)
                Text("Add Task / GitHub Issue")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
                Button(action: {
                    viewModel.isNewIssueModalPresented = false
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.title3)
                }
                .buttonStyle(.plain)
            }
            .padding(.bottom, 4)

            // Target Repo
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Target Repository / Project")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("Pre-selected from row")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary.opacity(0.8))
                }
                Picker("", selection: $selectedRepo) {
                    ForEach(availableRepos, id: \.self) { repo in
                        Text(repo).tag(repo)
                    }
                }
                .labelsHidden()
                .pickerStyle(.menu)
            }

            // Title
            VStack(alignment: .leading, spacing: 4) {
                Text("Issue / Task Title *")
                    .font(.caption)
                    .foregroundColor(.secondary)
                TextField("e.g. Implement webhook signature verification", text: $title)
                    .textFieldStyle(.roundedBorder)
            }

            // PRS Rating Override
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("PRS Rating Override (1–400)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("Default: 200")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.cyan)
                }
                TextField("200 (Neutral baseline)", text: $prsText)
                    .textFieldStyle(.roundedBorder)

                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text("PRS 4-Axis Rating Scale (GH-108):")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(.white.opacity(0.8))
                        Spacer()
                        Text("1–400 Total")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.cyan)
                    }
                    Text("Sum of 4 axes (1–100 each): Priority + Severity + Appeal + Effort. Neutral midpoint = 200.")
                        .font(.system(size: 9))
                        .foregroundColor(.secondary)
                }
                .padding(6)
                .background(Color.black.opacity(0.3))
                .cornerRadius(6)
            }

            // Description
            VStack(alignment: .leading, spacing: 4) {
                Text("Description / Acceptance Criteria (Optional)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                TextField("Reproduction steps, scope bounds, or expected behavior...", text: $descriptionText)
                    .textFieldStyle(.roundedBorder)
            }

            // Actions
            HStack {
                Spacer()
                Button("Cancel") {
                    viewModel.isNewIssueModalPresented = false
                }
                .keyboardShortcut(.cancelAction)

                Button("Create Issue") {
                    let trimmedTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !trimmedTitle.isEmpty else { return }
                    let prsVal = Int(prsText.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 200
                    let clampedPRS = max(1, min(400, prsVal))
                    viewModel.createIssueSimulated(
                        repo: selectedRepo,
                        title: trimmedTitle,
                        prs: clampedPRS,
                        description: descriptionText
                    )
                }
                .buttonStyle(.borderedProminent)
                .tint(.cyan)
                .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .keyboardShortcut(.defaultAction)
            }
            .padding(.top, 6)
        }
        .padding(18)
        .frame(width: 420)
        .background(Color(red: 22/255, green: 27/255, blue: 34/255))
        .cornerRadius(12)
    }
}
