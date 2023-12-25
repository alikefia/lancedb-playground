# format and lint code (just and python)
fmt:
    #!/usr/bin/env bash
    just --unstable --fmt
    ruff format py
    ruff check --fix py

# install deps
deps:
    #!/usr/bin/env bash
    pip install -U pip
    pip install -U -r requirements.txt
    pip install -U -r requirements.dev.txt

@build:
    (cd deps/lance/python && maturin develop)
    (cd deps/lancedb/python && pip install -e .)

# run main python commandline
@run *ARGS:
    python "${ROOT}/py/main.py" {{ ARGS }}

# make a full test
e2e:
    #!/usr/bin/env bash
    rm -rf "${ROOT}/data"
    just run db-init
    just run db-info
    just run q-init
    just run q-info
    just run q-knn
    just run q-ann
