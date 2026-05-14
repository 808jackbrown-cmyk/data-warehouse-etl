import os, logging
import pandas as pd
import sqlalchemy as sa
from pathlib import Path
from typing import Optional
import yaml

logger = logging.getLogger(__name__)

def load_config(config_path="config/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

class CRMExtractor:
    def __init__(self, config):
        self.path = Path(config["sources"]["crm"]["path"])
    def extract_accounts(self):
        return pd.read_csv(self.path / "accounts.csv", dtype={"account_id": str})
    def extract_contacts(self):
        return pd.read_csv(self.path / "contacts.csv", dtype={"contact_id": str})
    def extract_pipeline(self):
        return pd.read_csv(self.path / "opportunities.csv", dtype={"opp_id": str})

class FinancialExtractor:
    def __init__(self, config):
        self.engine = sa.create_engine("sqlite:///data/sample.db")
    def extract_invoices(self, since=None):
        return pd.read_sql("SELECT * FROM raw_invoices", self.engine)

class OperationalExtractor:
    def __init__(self, config):
        self.engine = sa.create_engine("sqlite:///data/sample.db")
    def extract_orders(self, since=None):
        return pd.read_sql("SELECT * FROM raw_orders", self.engine)
    def extract_order_lines(self, since=None):
        return pd.read_sql("SELECT * FROM raw_order_lines", self.engine)
    def extract_products(self):
        return pd.read_sql("SELECT * FROM raw_products", self.engine)

def extract_all(config, since=None):
    crm = CRMExtractor(config)
    fin = FinancialExtractor(config)
    ops = OperationalExtractor(config)
    logger.info("Extracting all sources...")
    raw = {
        "crm_accounts":    crm.extract_accounts(),
        "crm_contacts":    crm.extract_contacts(),
        "crm_pipeline":    crm.extract_pipeline(),
        "fin_invoices":    fin.extract_invoices(since),
        "ops_orders":      ops.extract_orders(since),
        "ops_order_lines": ops.extract_order_lines(since),
        "ops_products":    ops.extract_products(),
    }
    total = sum(len(df) for df in raw.values())
    logger.info(f"Extraction complete — {total:,} total records")
    return raw
