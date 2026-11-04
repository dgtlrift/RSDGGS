#!/bin/sh
# RSDGGS's releases with release-plz (release-plz.toml), and the generated documents
# attached to each. `pr`, `release` and `preview` need release-plz and a Rust toolchain on
# the PATH (the ariel-sim dev image, arisim-dev, has release-plz 0.3.171 and cddlc);
# `assets` needs gh. All but `preview` need GIT_TOKEN (for example "$(gh auth token)").
#   scripts/release.sh pr       opens or updates the release PR: next version, CHANGELOG.md
#   scripts/release.sh release  after that PR is merged: tags v<version>, makes the release
#   scripts/release.sh assets   attaches to the release of the tag at HEAD the draft's
#                               renderings (.txt, .html, .docx; not its XML source), the
#                               images (PNG and SVG) as one archive, and SHA256SUMS
#   scripts/release.sh preview  writes the next version and changelog locally, to look at
# Release PRs come only from here (Actions may not open pull requests); once one is merged,
# .github/workflows/release-plz.yml makes the release and attaches the assets, or
# `release` and `assets` above do.
set -eu
cd "$(dirname "$0")/.."
git config --global --add safe.directory "$PWD"
case "${1:-}" in
  pr) exec release-plz release-pr --git-token "${GIT_TOKEN:?set GIT_TOKEN}" --forge github ;;
  release) exec release-plz release --git-token "${GIT_TOKEN:?set GIT_TOKEN}" --forge github ;;
  preview) exec release-plz update ;;
  assets)
    tag="$(git describe --tags --exact-match HEAD)"
    # The draft revision draft/build.sh renders.
    name="$(sed -n 's/^name=//p' draft/build.sh)"
    out="$(mktemp -d)"
    for ext in txt html docx; do
      cp "draft/$name.$ext" "$out/"
    done
    images="rsdggs-images-$tag"
    mkdir "$out/$images"
    git ls-files -z 'images/*.png' 'images/*.svg' | xargs -0 cp --parents -t "$out/$images"
    tar -czf "$out/$images.tar.gz" -C "$out" "$images"
    (cd "$out" && sha256sum "$name".* "$images.tar.gz" > SHA256SUMS)
    GH_TOKEN="${GIT_TOKEN:?set GIT_TOKEN}" gh release upload "$tag" \
      "$out/$name.txt" "$out/$name.html" "$out/$name.docx" "$out/$images.tar.gz" \
      "$out/SHA256SUMS" --clobber
    cat "$out/SHA256SUMS"
    ;;
  *)
    echo "usage: scripts/release.sh pr | release | assets | preview" >&2
    exit 2
    ;;
esac
