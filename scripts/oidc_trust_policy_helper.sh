#!/usr/bin/env bash

set -euo pipefail

# Simple interactive helper to review and update GitHub OIDC trust policy
# - Shows current trust policy of a role
# - Generates a proposed trust policy for the given repo/branch
# - Optionally applies the update via aws iam update-assume-role-policy
#
# Prerequisites:
# - AWS CLI v2 configured with permissions to read/update IAM roles
# - jq (optional). If missing, JSON is still shown via python pretty print

log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*" 1>&2; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log_error "Command not found: $1"; exit 1
  fi
}

json_pp() {
  # Pretty-print JSON using jq if available, else python
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    python3 - <<'PY'
import sys, json
print(json.dumps(json.loads(sys.stdin.read()), indent=2, ensure_ascii=False))
PY
  fi
}

urldecode_json_pp() {
  python3 - <<'PY'
import sys, json, urllib.parse
raw = sys.stdin.read()
decoded = urllib.parse.unquote(raw)
try:
    obj = json.loads(decoded)
    print(json.dumps(obj, indent=2, ensure_ascii=False))
except Exception:
    # Fallback: print as-is
    print(decoded)
PY
}

prompt() {
  local msg="$1" default="${2:-}"
  if [[ -n "$default" ]]; then
    read -r -p "$msg [$default]: " input || true
    echo "${input:-$default}"
  else
    read -r -p "$msg: " input || true
    echo "$input"
  fi
}

confirm() {
  read -r -p "$* [y/N]: " ans || true
  case "${ans:-}" in
    y|Y|yes|YES) return 0;;
    *) return 1;;
  esac
}

# --- Preconditions
require_cmd aws
require_cmd python3

AWS_REGION_DEFAULT="${AWS_REGION:-ap-northeast-1}"
ACCOUNT_ID_DEFAULT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
ROLE_NAME_DEFAULT="GitHubActions-ExcelUnlocker-development"
REPO_SLUG_DEFAULT="hirokun-hub/python-excel-unlocker"

log_info "This helper will review and optionally update the trust policy for a GitHub OIDC role."
AWS_REGION=$(prompt "AWS Region" "$AWS_REGION_DEFAULT")
ACCOUNT_ID=$(prompt "AWS Account ID" "$ACCOUNT_ID_DEFAULT")
ROLE_NAME=$(prompt "OIDC Role name" "$ROLE_NAME_DEFAULT")
REPO_SLUG=$(prompt "GitHub repo (OWNER/REPO) for OIDC" "$REPO_SLUG_DEFAULT")

if confirm "Restrict to a single branch (e.g., main)?"; then
  BRANCH=$(prompt "Branch name" "main")
  SUB_CONDITION="repo:${REPO_SLUG}:ref:refs/heads/${BRANCH}"
else
  SUB_CONDITION="repo:${REPO_SLUG}:*"
fi

if [[ -z "$ACCOUNT_ID" ]]; then
  log_error "AWS Account ID is required"; exit 1
fi

export AWS_REGION

# --- Check OIDC provider presence
OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers \
  --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" \
  --output text 2>/dev/null || true)

if [[ -z "$OIDC_PROVIDER_ARN" ]]; then
  log_warn "GitHub OIDC provider not found in account ${ACCOUNT_ID}. Create it before proceeding."
else
  log_info "Detected OIDC provider: $OIDC_PROVIDER_ARN"
fi

# --- Fetch current trust policy
log_info "Fetching current trust policy for role: ${ROLE_NAME}"
if ! CURRENT_URLENC=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' --output text 2>/dev/null); then
  log_error "Role not found: $ROLE_NAME"; exit 1
fi

log_info "Current trust policy (decoded):"
printf '%s' "$CURRENT_URLENC" | urldecode_json_pp || true

# --- Build proposed trust policy
read -r -d '' TRUST_POLICY <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "${SUB_CONDITION}"
        }
      }
    }
  ]
}
JSON

log_info "Proposed trust policy:"
printf '%s\n' "$TRUST_POLICY" | json_pp

if confirm "Apply this trust policy to role '${ROLE_NAME}'?"; then
  log_info "Updating assume role policy..."
  aws iam update-assume-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-document "$TRUST_POLICY" >/dev/null
  log_info "Update completed. Verifying..."
  NEW_URLENC=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' --output text)
  printf '%s' "$NEW_URLENC" | urldecode_json_pp || true
  log_info "Done."
else
  log_warn "No changes applied."
fi

log_info "Next steps:"
echo "1) Ensure GitHub secret AWS_GITHUB_ACTIONS_ROLE_ARN points to arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "2) Re-run the GitHub Actions workflow (environment=development)"



