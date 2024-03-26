# Variables
$user = "NickHugi"  # Replace with your GitHub username
$repo = "PyKotor"  # Replace with your repository name
$workflowsDir = "./workflows"  # Adjust the path to your local clone of the repository

# Whitelist of workflow filenames to exclude from deletion (just the filenames, not full path)
$whitelist = @()

# Authenticate with GitHub CLI (if necessary)
#gh auth login

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
            # Modified line to include status and conclusion in the output
            $runs = gh api repos/$user/$repo/actions/workflows/$workflowId/runs --jq ".workflow_runs[] | {id: .id, status: .status, conclusion: .conclusion}" --paginate | ConvertFrom-Json
            foreach ($run in $runs) {
                # Check if the run was cancelled
                if ($run.status -eq 'completed' -and $run.conclusion -eq 'cancelled') {
                    Write-Output "Deleting canceled run '$($run.id)' from workflow '$workflowFile'..."
                    gh api --method DELETE -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "repos/$user/$repo/actions/runs/$($run.id)"
                } elseif ($run.status -eq 'completed' -and $run.conclusion -eq 'startup_failure') {
                    Write-Output "Deleting run '$($run.id)' that failed to start, workflow '$workflowFile'..."
                    gh api --method DELETE -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "repos/$user/$repo/actions/runs/$($run.id)"
                } else {
                    Write-Output "Skipping run '$($run.id)' from workflow '$workflowFile' with status '$($run.status)' and conclusion '$($run.conclusion)'"
                }
            }
        }
    }
}
