# Cargo Diff Utility

Quickly generate diffs from one version of a cargo crate to another.

Shamelessly adopted from @mimoo's [gist](https://gist.github.com/mimoo/fb88d33889d236d937fa1c6946698341)

## Quick Setup

### Build

**Docker**
- run `make build`

### Running

**Diff between two versions of a crate from crates.io**
- run `./create-cratesio-diff.sh {crate_name} {version_1} {version_2}` (e.g. `./create-cratesio-diff.sh tokio 0.2.22 0.3.4`)

**Diff between git repo and crates.io package tar archive at a specific version**
- run `./create-git-crate-diff.sh <crate_name> <version>

You should see an HTML report file with the naming scheme `{crate_name}.{version_1}-{version_2}.html` in your current directory.
