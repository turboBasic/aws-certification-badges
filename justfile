default:
    @just --list

# Bootstrap mise first; this also refreshes tools on later setup runs.
setup:
    mise install
    mise run deps
    prek install

deps:
    mise run deps

lint:
    mise run lint

fmt:
    mise run fmt

typecheck:
    mise run typecheck

test *args:
    mise run test -- {{args}}

build:
    mise run build

ci:
    mise run ci
