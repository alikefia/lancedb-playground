# format and lint code (just and python)
fmt:
    #!/usr/bin/env bash
    just --unstable --fmt
    isort "${ROOT}/src"
    black "${ROOT}/src"
    ruff check "${ROOT}/src"

# run main python commandline
@do *ARGS:
    python "${ROOT}/src/main.py" {{ ARGS }}

# make a full test
e2e:
    #!/usr/bin/env bash
    rm -rf "${ROOT}/data"
    just do db-init
    just do db-info
    just do q-init
    just do q-info
    just do q-knn
    just do q-ann
