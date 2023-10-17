import logging
import os
import time
from functools import wraps
from pathlib import Path
from random import random, seed

import lancedb
import pyarrow as pa
import pyarrow.parquet as pq
import typer

log_level = os.environ.get("LOG_LEVEL", "info")
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format="%(asctime)s %(levelname)s | %(processName)s %(name)s | %(message)s",
)


logger = logging.getLogger(__name__)
app = typer.Typer()


V_SIZE = 256

DB_PATH = "benchmark"
DB_TABLE = "vectors"
DB_TABLE_SIZE = os.environ.get("DB_TABLE_SIZE", 100000)

Q_PATH = "query"
Q_SIZE = os.environ.get("Q_SIZE", 100)
Q_V = "v.parquet"
Q_KNN = "knn.parquet"
Q_ANN = "ann.parquet"


def timeit(func):
    @wraps(func)
    def f(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"{func.__name__} {args} done in {total_time:.2f} secs")
        return result

    return f


def get_db():
    if int(os.environ["AZURE"]) == 0:
        f = Path(os.environ["DATA"])
        f.mkdir(parents=True, exist_ok=True)
        return lancedb.connect(f / DB_PATH)
    else:
        return lancedb.connect(
            f"az://{os.environ['AZURE_STORAGE_CONTAINER']}/{DB_PATH}"
        )


def get_q(what="v"):
    tables = {
        "v": Q_V,
        "knn": Q_KNN,
        "ann": Q_ANN,
    }
    f = Path(os.environ["DATA"]) / Q_PATH
    f.mkdir(parents=True, exist_ok=True)
    return f / tables[what]


def gen_data(n: int, start=1):
    seed()
    for i in range(start, start + n):
        yield ({"id": i, "vector": list(random() for _ in range(V_SIZE))})


@app.command()
def db_init(n: int = DB_TABLE_SIZE):
    get_db().create_table(DB_TABLE, data=list(gen_data(n)))


@app.command()
def db_info():
    logger.debug(get_db().open_table(DB_TABLE).head(10))


@app.command()
def db_add(n: int, start: int):
    get_db().open_table(DB_TABLE).add(list(gen_data(n, start=start)))


@app.command()
def q_init(n: int = Q_SIZE):
    pq.write_table(pa.Table.from_pylist(list(gen_data(n))), get_q())


@app.command()
def q_info():
    logger.debug(pq.read_table(get_q()))


@timeit
def q_process(what: str):
    table = get_db().open_table(DB_TABLE)
    r = pa.Table.from_pylist(
        [
            {
                "id": v["id"],
                "neighbours": table.search(v["vector"])
                .limit(10)
                .select(["id"])
                .to_arrow()["id"]
                .to_pylist(),
            }
            for v in pq.read_table(get_q()).to_pylist()
        ]
    )
    pq.write_table(r, get_q(what))


@app.command()
@timeit
def create_index():
    get_db().open_table(DB_TABLE).create_index(
        num_sub_vectors=8
    )  # TODO :avoid hard coded params


@app.command()
def q_knn():
    q_process("knn")


@app.command()
def q_ann():
    create_index()
    q_process("ann")


if __name__ == "__main__":
    app()
