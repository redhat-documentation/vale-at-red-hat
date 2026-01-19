#!/bin/bash
#
# Compare Vale errors before and after rule changes
# Usage: ./tools/compare-errors.sh <rule-name> <repo-url>
# Example: ./tools/compare-errors.sh Spelling https://github.com/openshift/openshift-docs
#

set -e

# Check for required arguments
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <rule-name> <repo-url>"
    echo "Example: $0 Spelling https://github.com/aireilly/mcp-test-repo"
    exit 1
fi

RULE_NAME="$1"
REPO_URL="$2"
FULL_RULE_NAME="RedHat.${RULE_NAME}"
RULE_FILE=".vale/styles/RedHat/${RULE_NAME}.yml"
REPO_NAME=$(basename "$REPO_URL" .git)

VALE_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="/tmp/vale-comparison"
BASE_REF="${BASE_REF:-upstream/main}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Create work directory
mkdir -p "$WORK_DIR"

# Function to clone or update the repo
clone_repo() {
    local repo_dir="$WORK_DIR/$REPO_NAME"

    if [[ -d "$repo_dir" ]]; then
        log_info "Using cached $REPO_NAME..."
    else
        log_info "Cloning $REPO_NAME (shallow)..."
        git clone --depth 1 --quiet "$REPO_URL" "$repo_dir" || {
            log_error "Failed to clone $REPO_NAME"
            return 1
        }
    fi

    printf '%s\n' "$repo_dir"
}


# Create a .vale.ini that uses the current repo's styles and enables the tested rule
create_config() {
    local temp_config="$WORK_DIR/.vale.ini"

    # Create config with absolute path to current repo's styles
    cat > "$temp_config" << EOF
StylesPath = $VALE_REPO_DIR/.vale/styles

MinAlertLevel = suggestion

IgnoredScopes = code, tt, img, url, a, body.id

SkippedScopes = script, style, pre, figure, code, tt, blockquote, listingblock, literalblock

Packages = RedHat

[[!.]*.adoc]
BasedOnStyles = RedHat
${FULL_RULE_NAME} = YES

[*.md]
BasedOnStyles = RedHat
${FULL_RULE_NAME} = YES
TokenIgnores = (\x60[^\n\x60]+\x60), ([^\n]+=[^\n]*), (\+[^\n]+\+), (http[^\n]+\[)
EOF

    echo "$temp_config"
}

# Function to run Vale and extract errors for the specified rule
run_vale_check() {
    local target_dir="$1"
    local output_file="$2"
    local config_file="$3"
    local repo_name
    repo_name=$(basename "$target_dir")

    log_info "Running Vale ($FULL_RULE_NAME) on $repo_name..."

    # Run Vale and extract only errors for the specified rule
    # Output: count + word (for summary)
    vale --config="$config_file" \
         --output=JSON \
         "$target_dir" 2>/dev/null | \
    jq -r --arg rule "$FULL_RULE_NAME" '.[][] | select(.Check == $rule) | "\(.Match)"' | \
    sort | uniq -c | sort -rn > "$output_file" || true

    # Detailed output with file paths (extract path from object keys)
    vale --config="$config_file" \
         --output=JSON \
         "$target_dir" 2>/dev/null | \
    jq -r --arg rule "$FULL_RULE_NAME" 'to_entries[] | .key as $file | .value[] | select(.Check == $rule) | "\($file):\(.Line): \(.Match) - \(.Message)"' | \
    sort > "${output_file}.detailed" || true
}

# Function to compare results
compare_results() {
    local upstream_file="$1"
    local current_file="$2"

    local upstream_count
    local current_count
    upstream_count=$(awk '{sum += $1} END {print sum+0}' "$upstream_file")
    current_count=$(awk '{sum += $1} END {print sum+0}' "$current_file")
    local diff=$((upstream_count - current_count))

    echo ""
    echo "=============================================="
    echo -e "${BLUE}Results for: $REPO_NAME ($FULL_RULE_NAME)${NC}"
    echo "=============================================="
    echo ""
    echo -e "Errors with ${BASE_REF} rule:  ${RED}$upstream_count${NC}"
    echo -e "Errors with current rule:   ${GREEN}$current_count${NC}"
    echo ""

    if [[ $diff -gt 0 ]]; then
        if [[ $upstream_count -gt 0 ]]; then
            log_success "Your changes reduced errors by $diff ($(echo "scale=1; $diff * 100 / $upstream_count" | bc)%)"
        else
            log_success "Your changes reduced errors by $diff"
        fi
    elif [[ $diff -lt 0 ]]; then
        log_warn "Your changes increased errors by $((-diff))"
    else
        log_info "No change in error count"
    fi
}

# Main execution
main() {
    local rule_path="$VALE_REPO_DIR/$RULE_FILE"

    # Check rule file exists
    if [[ ! -f "$rule_path" ]]; then
        log_error "Rule file not found: $rule_path"
        exit 1
    fi

    log_info "Vale repository: $VALE_REPO_DIR"
    log_info "Rule: $FULL_RULE_NAME"
    log_info "Rule file: $RULE_FILE"
    log_info "Base ref: $BASE_REF"
    log_info "Work directory: $WORK_DIR"
    log_info "Test repo: $REPO_URL"
    echo ""

    # Save current version of the rule
    cp "$rule_path" "$WORK_DIR/${RULE_NAME}.yml.current"

    # Get the upstream/main version of the rule
    log_info "Getting $BASE_REF version of $RULE_FILE..."
    if ! git -C "$VALE_REPO_DIR" show "${BASE_REF}:${RULE_FILE}" > "$WORK_DIR/${RULE_NAME}.yml.upstream" 2>/dev/null; then
        log_error "Could not get $BASE_REF version of $RULE_FILE"
        log_error "Make sure upstream remote exists: git remote add upstream https://github.com/redhat-documentation/vale-at-red-hat.git && git fetch upstream"
        exit 1
    fi

    # Create config
    config_file=$(create_config)
    log_info "Using config: $config_file"

    # Clone the target repo
    log_info "Processing $REPO_NAME..."
    repo_dir=$(clone_repo)

    # Create output directory
    output_dir="$WORK_DIR/results/${RULE_NAME}/$REPO_NAME"
    mkdir -p "$output_dir"

    # Run with UPSTREAM version of the rule
    log_info "Testing with $BASE_REF version of rule..."
    cp "$WORK_DIR/${RULE_NAME}.yml.upstream" "$rule_path"
    run_vale_check "$repo_dir" "$output_dir/upstream.txt" "$config_file"

    # Run with CURRENT version of the rule
    log_info "Testing with current version of rule..."
    cp "$WORK_DIR/${RULE_NAME}.yml.current" "$rule_path"
    run_vale_check "$repo_dir" "$output_dir/current.txt" "$config_file"

    # Restore current version
    cp "$WORK_DIR/${RULE_NAME}.yml.current" "$rule_path"

    # Compare and display results
    compare_results "$output_dir/upstream.txt" "$output_dir/current.txt"

    echo ""
    echo "=============================================="
    log_success "Comparison complete!"
    echo "=============================================="
    echo ""
    echo "diff $output_dir/upstream.txt $output_dir/current.txt"
    echo ""
    echo "less $output_dir/current.txt.detailed"
}

main
