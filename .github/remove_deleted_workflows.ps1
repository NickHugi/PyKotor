# Variables
$user = "NickHugi"  # Replace with your GitHub username
$repo = "PyKotor"  # Replace with your repository name
$workflowsDir = "./workflows"  # Adjust the path to your local clone of the repository

# Whitelist of workflow filenames to exclude from deletion (just the filenames, not full path)
$whitelist = @("compile_and_test_pykotor.yml", "publish_and_test_pykotor.yml", "publish_pykotor.yml", "run_and_report_pytests.yml")

# Authenticate with GitHub CLI (if necessary)
#gh auth login

# Step 1: Identify Non-Existent Workflows
# Fetch list of all workflows from GitHub
gh api repos/$user/$repo/actions/workflows --paginate | Out-File -FilePath all_workflows.json

# Fetch all workflows from GitHub
$allWorkflows = gh api repos/$user/$repo/actions/workflows --paginate | ConvertFrom-Json

# Process workflows
foreach ($workflow in $allWorkflows.workflows) {
    $workflowFile = $workflow.path -replace '.github/workflows/', ''
    $localPath = Join-Path -Path $workflowsDir -ChildPath $workflowFile

    if (-not (Test-Path -Path $localPath) -and -not ($whitelist -contains $workflowFile)) {
        $workflowId = $workflow.id
        if ($workflowId) {
            Write-Output "Fetch workflow runs for workflow $workflowFile id $workflowId"
            $runs = gh api repos/$user/$repo/actions/workflows/$workflowId/runs --jq ".workflow_runs[] | {id: .id}" --paginate | ConvertFrom-Json
            if ($runs -and $runs.Count -gt 0) {
                foreach ($run in $runs) {
                    Write-Output "Deleting run '$($run.id)' from workflow '$workflowFile'..."
                    gh api --method DELETE -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "repos/$user/$repo/actions/runs/$($run.id)"
                }
            }
        }
    }
}
