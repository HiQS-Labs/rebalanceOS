-- Recomputation of the PR #308 working-doc corpus fractions on a different
-- device's snapshot (2026-10-03). Suppression here is LIKE-based: an UPPER
-- bound of the code's boundary-regex behavior. Resolved rows approximated by
-- MAX(fetched_at) per (repo, item_type, number).
.headers on
.mode column
SELECT d.repo_full_name, COUNT(*) AS total_commits,
       SUM(CASE WHEN d.ref = ('refs/heads/' || m.default_branch) THEN 1 ELSE 0 END) AS default_branch_commits
FROM github_direct_commits d JOIN github_repo_meta m
  ON LOWER(d.repo_full_name) = LOWER(m.repo_full_name)
GROUP BY 1 HAVING total_commits > 10000;

CREATE TEMP VIEW resolved AS
SELECT * FROM github_items gi WHERE fetched_at = (
  SELECT MAX(fetched_at) FROM github_items g2
  WHERE g2.repo_full_name=gi.repo_full_name AND g2.item_type=gi.item_type AND g2.number=gi.number);
CREATE TEMP VIEW cands AS
SELECT i.repo_full_name, i.number, i.created_at FROM resolved i
WHERE i.item_type='issue' AND i.state='closed'
  AND LOWER(COALESCE(i.state_reason,'')) IN ('', 'completed')
  AND i.closed_at IS NOT NULL
  AND julianday('2026-10-03T04:20:00Z') - julianday(i.closed_at) <= 30
  AND NOT EXISTS (
    SELECT 1 FROM github_links l JOIN resolved p
      ON p.repo_full_name=l.repo_full_name AND p.item_type='pull_request' AND p.number=l.source_number
    WHERE l.repo_full_name=i.repo_full_name AND l.source_type='pull_request'
      AND l.target_type='issue' AND l.target_number=i.number AND p.is_merged=1);
SELECT COUNT(*) AS candidates_all_repos FROM cands;
SELECT 'suppressed_all' AS scope, COUNT(*) FROM cands c WHERE EXISTS (
  SELECT 1 FROM github_direct_commits d
  WHERE LOWER(d.repo_full_name)=LOWER(c.repo_full_name)
    AND d.ref = (SELECT 'refs/heads/' || m.default_branch FROM github_repo_meta m WHERE LOWER(m.repo_full_name)=LOWER(c.repo_full_name))
    AND (d.message LIKE '%#' || c.number || '%' OR UPPER(d.message) LIKE '%GH-' || c.number || '%')
    AND julianday(d.committed_at) >= julianday(c.created_at));
