import logging
from datetime import datetime, timezone
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text

logger = logging.getLogger(__name__)
NOW = datetime.now(timezone.utc)

class WarehouseLoader:
    def __init__(self, engine):
        self.engine = engine

    def upsert(self, df, table, key_col, chunk_size=5000):
        df = df.copy()
        df["etl_loaded_at"] = NOW
        staging = f"stg_{table}"
        with self.engine.begin() as conn:
            df.to_sql(staging, conn, if_exists="replace", index=False, chunksize=chunk_size)
            try:
                conn.execute(text(f"DELETE FROM {table} WHERE {key_col} IN (SELECT {key_col} FROM {staging})"))
            except Exception:
                pass
            cols = ", ".join(df.columns)
            try:
                conn.execute(text(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM {staging}"))
            except Exception:
                df.to_sql(table, conn, if_exists="replace", index=False, chunksize=chunk_size)
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {staging}"))
            except Exception:
                pass
        logger.info(f"  Loaded '{table}': {len(df):,} rows")

def load_all(transformed, engine):
    loader = WarehouseLoader(engine)
    for table, df in transformed.items():
        key = "customer_id" if "customer" in table else \
              "order_id"    if "order"    in table else \
              "product_id"  if "product"  in table else "opp_id"
        loader.upsert(df, table, key)
    logger.info("All tables loaded.")
