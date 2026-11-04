#!/bin/sh
# RSDGGS's releases with release-plz (release-plz.toml). Needs release-plz and a Rust
# toolchain on the PATH (the ariel-sim dev image, arisim-dev, has release-plz 0.3.171 and
# cddlc), and GIT_TOKEN (for example "$(gh auth token)").
#   scripts/release.sh pr       opens or updates the release PR: next version, CHANGELOG.md
#   scripts/release.sh release  after that PR is merged: tags v<version>, makes the release
#   scripts/release.sh preview  writes the next version and changelog locally, to look at
# Release PRs come only from here (Actions may not open pull requests); once one is merged,
# .github/workflows/release-plz.yml makes the release, or `release` above does.
set -eu
cd "$(dirname "$0")/.."
git config --global --add safe.directory "$PWD"
case "${1:-}" in
  pr) exec release-plz release-pr --git-token "${GIT_TOKEN:?set GIT_TOKEN}" --forge github ;;
  release) exec release-plz release --git-token "${GIT_TOKEN:?set GIT_TOKEN}" --forge github ;;
  preview) exec release-plz update ;;
  *)
    echo "usage: scripts/release.sh pr | release | preview" >&2
    exit 2
    ;;
esac
