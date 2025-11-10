#!/bin/bash
# Script to update all submodules in the repository with optional fork synchronization

set -o pipefail

C_RESET="\033[0m"
C_INFO="\033[36m"
C_SUCCESS="\033[32m"
C_WARN="\033[33m"
C_ERROR="\033[31m"

print_info() {
    printf "%b%s%b\n" "$C_INFO" "$1" "$C_RESET"
}

print_success() {
    printf "%b%s%b\n" "$C_SUCCESS" "$1" "$C_RESET"
}

print_warning() {
    printf "%b%s%b\n" "$C_WARN" "$1" "$C_RESET"
}

print_error() {
    printf "%b%s%b\n" "$C_ERROR" "$1" "$C_RESET"
}

readarray -t SUBMODULES < <(git config --file .gitmodules --get-regexp path 2>/dev/null | awk '{print $2}' | sort -u)

print_info "Updating all submodules..."

if [ ${#SUBMODULES[@]} -eq 0 ]; then
    print_warning "No submodules found in this repository."
    exit 0
fi

print_info "Found ${#SUBMODULES[@]} submodule(s): ${SUBMODULES[*]}"

GH_AVAILABLE=0
if command -v gh >/dev/null 2>&1; then
    GH_AVAILABLE=1
else
    print_warning "GitHub CLI (gh) is not available; fork detection will be limited."
fi

updated_count=0
skipped_count=0
failed_count=0

resolve_repo_identifier() {
    local url="$1"
    if [[ -z "$url" ]]; then
        return 1
    fi

    if [[ $url =~ github\.com[:/]([^/]+)/([^/]+?)(\.git)?$ ]]; then
        printf '%s/%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
        return 0
    fi

    return 1
}

determine_target_branch() {
    local current_branch="$1"
    local remote_head="$2"
    shift 2
    local -a remote_branches=("$@")

    local candidates=()
    if [[ -n "$current_branch" ]]; then candidates+=("$current_branch"); fi
    if [[ -n "$remote_head" ]]; then candidates+=("$remote_head"); fi
    candidates+=("main" "master")

    local candidate
    for candidate in "${candidates[@]}"; do
        if [[ -n "$candidate" ]] && printf '%s\n' "${remote_branches[@]}" | grep -qx "origin/$candidate"; then
            printf '%s' "$candidate"
            return 0
        fi
    done

    return 1
}

get_upstream_url() {
    local origin_url="$1"
    local parent_full="$2"

    if [[ -z "$parent_full" ]]; then
        return 1
    fi

    if [[ $origin_url == git@github.com:* ]]; then
        printf 'git@github.com:%s.git' "$parent_full"
    else
        printf 'https://github.com/%s.git' "$parent_full"
    fi
}

for submodule in "${SUBMODULES[@]}"; do
    print_info "Updating submodule: $submodule"

    if [[ ! -d "$submodule" ]]; then
        print_warning "  Submodule path '$submodule' does not exist locally. Skipping."
        ((skipped_count++))
        continue
    fi

    pushd "$submodule" >/dev/null 2>&1 || {
        print_warning "  Unable to enter submodule directory '$submodule'. Skipping."
        ((skipped_count++))
        continue
    }

    origin_url=$(git config --get remote.origin.url 2>/dev/null)
    if [[ -z "$origin_url" ]]; then
        print_warning "  Unable to determine origin URL. Skipping."
        popd >/dev/null
        ((skipped_count++))
        continue
    fi

    repo_identifier=""
    if repo_identifier=$(resolve_repo_identifier "$origin_url"); then
        :
    else
        repo_identifier=""
    fi

    mapfile -t remote_branches < <(git ls-remote --heads origin 2>/dev/null | awk '{sub("refs/heads/","", $2); print "origin/" $2}')
    if [[ ${#remote_branches[@]} -eq 0 ]]; then
        print_warning "  No remote branches detected on origin. Skipping."
        popd >/dev/null
        ((skipped_count++))
        continue
    fi

    current_branch=$(git branch --show-current 2>/dev/null | tr -d '\r')
    remote_head=$(git remote show origin 2>/dev/null | awk -F': ' '/HEAD branch/ {print $2; exit}')

    target_branch=""
    if target_branch=$(determine_target_branch "$current_branch" "$remote_head" "${remote_branches[@]}"); then
        :
    else
        print_warning "  Unable to determine a branch to update. Skipping."
        popd >/dev/null
        ((skipped_count++))
        continue
    fi

    if [[ "$current_branch" != "$target_branch" ]]; then
        if ! git checkout "$target_branch" >/dev/null 2>&1; then
            if ! git checkout -B "$target_branch" "origin/$target_branch" >/dev/null 2>&1; then
                print_warning "  Unable to switch to branch '$target_branch'. Skipping."
                popd >/dev/null
                ((skipped_count++))
                continue
            fi
        fi
    fi

    if ! git fetch origin "$target_branch" >/dev/null 2>&1; then
        print_warning "  Failed to fetch origin/$target_branch. Skipping."
        popd >/dev/null
        ((skipped_count++))
        continue
    fi

    if ! pull_output=$(git pull --ff-only origin "$target_branch" 2>&1); then
        print_warning "  Unable to fast-forward with origin/$target_branch. Skipping."
        popd >/dev/null
        ((skipped_count++))
        continue
    fi

    if [[ "$pull_output" == *"Already up to date."* ]]; then
        print_info "  Origin already up to date for branch '$target_branch'."
    else
        print_success "  Updated from origin/$target_branch."
    fi

    fork_updated=0
    if (( GH_AVAILABLE )) && [[ -n "$repo_identifier" ]]; then
        if fork_info=$(gh api "repos/$repo_identifier" --jq '.fork, (.parent.full_name // ""), (.parent.default_branch // "")' 2>&1); then
            readarray -t fork_fields <<<"$fork_info"
            is_fork=${fork_fields[0]}
            parent_full=${fork_fields[1]}
            parent_default=${fork_fields[2]}

            if [[ "$is_fork" == "true" && -n "$parent_full" ]]; then
                upstream_url=$(get_upstream_url "$origin_url" "$parent_full")
                upstream_branch="$target_branch"
                if [[ -n "$parent_default" ]]; then
                    upstream_branch="$parent_default"
                fi

                temp_remote="__update_submodules_upstream__"
                git remote remove "$temp_remote" >/dev/null 2>&1

                if git remote add "$temp_remote" "$upstream_url" >/dev/null 2>&1 || git remote set-url "$temp_remote" "$upstream_url" >/dev/null 2>&1; then
                    if git fetch "$temp_remote" "$upstream_branch" >/dev/null 2>&1; then
                        merge_ref="$temp_remote/$upstream_branch"
                        if git rev-parse "$merge_ref" >/dev/null 2>&1; then
                            if git merge-base --is-ancestor "$merge_ref" HEAD >/dev/null 2>&1; then
                                print_info "  Upstream changes are already present locally."
                                fork_updated=1
                            elif git merge-base --is-ancestor HEAD "$merge_ref" >/dev/null 2>&1; then
                                if git merge --ff-only "$merge_ref" >/dev/null 2>&1; then
                                    print_success "  Fast-forwarded to match upstream/$upstream_branch."
                                    fork_updated=1
                                else
                                    print_warning "  Unable to fast-forward to upstream/$upstream_branch."
                                fi
                            else
                                if git merge --no-commit --no-ff "$merge_ref" >/dev/null 2>&1; then
                                    git merge --abort >/dev/null 2>&1
                                    if git merge --no-ff --no-edit "$merge_ref" >/dev/null 2>&1; then
                                        print_success "  Merged upstream/$upstream_branch without conflicts."
                                        fork_updated=1
                                    else
                                        git merge --abort >/dev/null 2>&1
                                        print_warning "  Merge with upstream/$upstream_branch failed."
                                    fi
                                else
                                    git merge --abort >/dev/null 2>&1
                                    print_warning "  Conflicts detected when merging upstream/$upstream_branch. Skipping fork update."
                                fi
                            fi

                            if (( fork_updated )); then
                                if git push origin "$target_branch" >/dev/null 2>&1; then
                                    print_success "  Pushed fork updates to origin/$target_branch."
                                else
                                    print_warning "  Failed to push updates back to origin/$target_branch."
                                    fork_updated=0
                                fi
                            fi
                        else
                            print_warning "  Upstream branch '$upstream_branch' does not exist."
                        fi
                    else
                        print_warning "  Failed to fetch upstream branch '$upstream_branch'."
                    fi
                else
                    print_warning "  Unable to add temporary upstream remote ($upstream_url)."
                fi

                git remote remove "$temp_remote" >/dev/null 2>&1

                if (( fork_updated == 0 )); then
                    print_warning "  Fork update skipped for '$submodule'."
                fi
            fi
        else
            print_warning "  Unable to query GitHub for fork information: $fork_info"
        fi
    fi

    popd >/dev/null
    ((updated_count++))

done

print_info "Submodule update summary:"
print_success "  Updated: $updated_count"
print_warning "  Skipped: $skipped_count"
print_info "  Failed: $failed_count"

if (( failed_count > 0 )); then
    exit 1
fi

print_success "✓ Submodule processing completed."
