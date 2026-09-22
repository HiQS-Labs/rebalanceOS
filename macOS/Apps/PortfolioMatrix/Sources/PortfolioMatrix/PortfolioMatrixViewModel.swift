import Foundation
import SwiftUI

@MainActor
public final class PortfolioMatrixViewModel: ObservableObject {
    @Published public var matrix: PortfolioMatrixResponse?
    @Published public var isLoading: Bool = false
    @Published public var isMutatingTask: Bool = false
    @Published public var errorMessage: String?
    @Published public var toastMessage: String?
    @Published public var isNewIssueModalPresented: Bool = false
    @Published public var selectedRepoForNewIssue: String = ""
    @Published public var connectedPort: Int? = nil

    private let client: PortfolioClient

    public init(client: PortfolioClient = PortfolioClient()) {
        self.client = client
    }

    public func refresh() async {
        isLoading = true
        errorMessage = nil
        do {
            let res = try await client.fetchMatrix()
            self.matrix = res
            self.connectedPort = client.activePort
        } catch {
            self.errorMessage = error.localizedDescription
            self.connectedPort = nil
        }
        isLoading = false
    }

    public func completeTask(_ task: MatrixTask, in project: MatrixProject) async {
        guard !isMutatingTask else { return }
        isMutatingTask = true
        errorMessage = nil

        let currentRev = matrix?.goals_revision
        do {
            _ = try await client.completeTask(
                title: task.title,
                lineIndex: task.line_index,
                revision: currentRev
            )
            showToast("✓ Completed: \(task.title)")
            await refresh()
        } catch ClientError.staleRevision {
            showToast("Task changed on server. Refreshing...")
            await refresh()
        } catch {
            errorMessage = error.localizedDescription
            // Ambiguous transport failure: dispatch recovery GET
            await refresh()
        }

        isMutatingTask = false
    }

    public func openNewIssueModal(for repo: String) {
        selectedRepoForNewIssue = repo
        isNewIssueModalPresented = true
    }

    public func createIssueSimulated(repo: String, title: String, prs: Int, description: String) {
        isNewIssueModalPresented = false
        showToast("✓ Simulated: Issue queued for \(repo) with PRS: \(prs)")
    }

    public func showToast(_ msg: String) {
        toastMessage = msg
        Task {
            try? await Task.sleep(nanoseconds: 3_500_000_000)
            if toastMessage == msg {
                toastMessage = nil
            }
        }
    }
}
