# Variables
user="GH_USERNAME"  # Replace with your GitHub username
repo="REPO_NAME"  # Replace with your repository name
workflows_dir="./workflows"  # Adjust the path to your local clone of the repository

# Authenticate with GitHub CLI (if necessary)
gh auth login

# Step 1: Identify Non-Existent Workflows
# Fetch list of all workflows from GitHub
gh api repos/$user/$repo/actions/workflows --paginate > all_workflows.json

# Extract workflow file names from GitHub
jq -r '.workflows[].path' all_workflows.json | sed 's|.github/workflows/||' > github_workflows.txt

# List .yml files in the local .github/workflows directory
ls $workflows_dir | grep '\.yml$' > local_workflows.txt

# Identify workflows that do not exist locally
grep -Fxv -f local_workflows.txt github_workflows.txt > non_existent_workflows.txt

# Step 2: Delete Runs for Identified Workflows
# For each non-existent workflow, find and delete its runs
while read -r workflow_file; do
  workflow_id=$(jq --arg file "$workflow_file" '.workflows[] | select(.path == "\(.github/workflows/\($file))").id' all_workflows.json)
  if [ ! -z "$workflow_id" ]; then
    # Fetch and delete runs for this workflow ID
    gh api repos/$user/$repo/actions/workflows/$workflow_id/runs --paginate -q '.workflow_runs[] | "\(.id)"' | \
    xargs -n1 -I % gh api repos/$user/$repo/actions/runs/% -X DELETE
  fi
done < non_existent_workflows.txt
