# format and lint code (just and python)
fmt:
    #!/usr/bin/env bash
    just --unstable --fmt
    isort "${ROOT}/src"
    black "${ROOT}/src"
    ruff check "${ROOT}/src"

# install deps
deps:
    #!/usr/bin/env bash
    pip install -U pip
    pip install -r requirements.txt
    pip install -r requirements.dev.txt
    (cd deps/lance/python && maturin develop)
    (cd deps/lancedb/python && pip install -e .)

@build:
    (cd deps/lance/python && maturin develop)

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
