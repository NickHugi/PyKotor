# Variables
$user = "th3w1zard1"  # Replace with your GitHub username
$repo = "PyKotor"  # Replace with your repository name
$workflowsDir = "./workflows"  # Adjust the path to your local clone of the repository

# Whitelist of workflow filenames to exclude from deletion (just the filenames, not full path)
$whitelist = @("compile_and_test_pykotor.yml")

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
            # Fetch and delete all workflow runs for this workflow ID
            $runs = gh api repos/$user/$repo/actions/workflows/$workflowId/runs --jq ".workflow_runs[] | {id: .id}" --paginate | ConvertFrom-Json
            if ($runs -and $runs.Count -gt 0) {
                foreach ($run in $runs) {
                    gh api -X DELETE -H "Accept: application/vnd.github+json" repos/$user/$repo/actions/workflows/$workflowId/runs/$run.id
                }
            }
        }
    }
}
