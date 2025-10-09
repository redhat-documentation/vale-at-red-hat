#!/usr/bin/env bash

set -euo pipefail

sync_sources() {
  # Keep local venv only
  if [[ "${CI:-}" == "true" ]]; then rm -rf .venv; fi
  if [[ ! -d .venv ]]; then
    python -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
}

build_site() {
  python -m mkdocs build -f mkdocs.yml --clean -v
}

serve_site() {
  python -m mkdocs serve -f mkdocs.yml
}

sync_sources

# Build in GitLab CI, otherwise serve locally
case "${1:-}" in
  --build) build_site ;;
  *)
    if [[ "${CI:-}" == "true" ]]; then
      build_site
    else
      serve_site
    fi
    ;;
esac
