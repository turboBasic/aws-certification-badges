default:
    @just --list

# Bootstrap mise first; this also refreshes tools on later setup runs.
setup:
    mise install
    just deps
    prek install

deps:
    uv sync --locked

# The separate typecheck command owns the full-tree check during validation.
lint: deps
    prek run --all-files --show-diff-on-failure --skip pyright

fmt: deps
    prek run ruff-format taplo-fmt --all-files --show-diff-on-failure

typecheck: deps
    uv run --locked pyright

test *args: deps
    uv run --locked pytest {{args}}

build: deps
    uv build
