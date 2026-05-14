import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def deduplicate(df, key, tiebreak_col="updated_at"):
    return df.sort_values(tiebreak_col, ascending=False).drop_duplicates(subset=[key])

def cast_dates(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df

def transform_customers(accounts, contacts):
    logger.info("Transforming customers...")
    accounts = accounts.copy()
    accounts.columns = accounts.columns.str.lower().str.strip()
    accounts = cast_dates(accounts, ["created_date", "updated_at"])
    accounts = deduplicate(accounts, "account_id")
    contacts = contacts.copy()
    contacts.columns = contacts.columns.str.lower().str.strip()
    primary = contacts.sort_values("updated_at", ascending=False).drop_duplicates("account_id")[["account_id","first_name","last_name","email","phone"]]
    df = accounts.merge(primary, on="account_id", how="left")
    rev = pd.to_numeric(df.get("annual_revenue", 0), errors="coerce").fillna(0)
    df["customer_segment"] = "startup"
    df.loc[rev >= 50_000, "customer_segment"] = "smb"
    df.loc[rev >= 250_000, "customer_segment"] = "mid_market"
    df.loc[rev >= 1_000_000, "customer_segment"] = "enterprise"
    df = df.rename(columns={"account_id": "customer_id", "account_name": "company_name", "billing_state": "state"})
    logger.info(f"  {len(df):,} customers transformed")
    return df

def transform_orders(orders, order_lines, invoices):
    logger.info("Transforming orders...")
    orders = orders.copy()
    orders.columns = orders.columns.str.lower().str.strip()
    orders = cast_dates(orders, ["order_date", "ship_date", "updated_at"])
    orders = deduplicate(orders, "order_id")
    lines = order_lines.copy()
    lines.columns = lines.columns.str.lower().str.strip()
    lines["line_revenue"] = pd.to_numeric(lines["quantity"], errors="coerce") * pd.to_numeric(lines["unit_price"], errors="coerce")
    lines["line_cogs"]    = pd.to_numeric(lines["quantity"], errors="coerce") * pd.to_numeric(lines["unit_cost"], errors="coerce")
    agg = lines.groupby("order_id").agg(gross_revenue=("line_revenue","sum"), total_cogs=("line_cogs","sum"), line_count=("order_id","count")).reset_index()
    orders = orders.merge(agg, on="order_id", how="left")
    orders["gross_margin"] = orders["gross_revenue"] - orders["total_cogs"]
    orders["margin_pct"] = np.where(orders["gross_revenue"] > 0, orders["gross_margin"] / orders["gross_revenue"], np.nan)
    inv = invoices.copy()
    inv.columns = inv.columns.str.lower().str.strip()
    inv_agg = inv.groupby("order_id").agg(invoice_amount=("invoice_amount","sum"), amount_paid=("amount_paid","sum")).reset_index()
    orders = orders.merge(inv_agg, on="order_id", how="left")
    orders["outstanding_balance"] = orders["invoice_amount"].fillna(0) - orders["amount_paid"].fillna(0)
    orders["payment_status"] = "uninvoiced"
    orders.loc[orders["invoice_amount"].notna(), "payment_status"] = "invoiced"
    orders.loc[orders["outstanding_balance"] <= 0.01, "payment_status"] = "paid"
    orders["days_to_ship"] = (orders["ship_date"] - orders["order_date"]).dt.days
    logger.info(f"  {len(orders):,} orders transformed")
    return orders

def transform_products(products):
    logger.info("Transforming products...")
    df = products.copy()
    df.columns = df.columns.str.lower().str.strip()
    df = deduplicate(df, "product_id")
    df["sku"] = df["sku"].str.upper().str.strip()
    df["is_active"] = df.get("status", pd.Series(["active"]*len(df))).str.lower() == "active"
    logger.info(f"  {len(df):,} products transformed")
    return df

def transform_pipeline(opps):
    logger.info("Transforming pipeline...")
    df = opps.copy()
    df.columns = df.columns.str.lower().str.strip()
    df = deduplicate(df, "opp_id")
    weights = {"prospecting":0.05,"qualification":0.10,"proposal":0.65,"negotiation":0.80,"closed won":1.0,"closed lost":0.0}
    df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0)
    df["stage_probability"] = df["stage_name"].str.lower().map(weights).fillna(0.25)
    df["weighted_value"] = df["amount"] * df["stage_probability"]
    logger.info(f"  {len(df):,} opportunities transformed")
    return df

def transform_all(raw):
    return {
        "dim_customers": transform_customers(raw["crm_accounts"], raw["crm_contacts"]),
        "fact_orders":   transform_orders(raw["ops_orders"], raw["ops_order_lines"], raw["fin_invoices"]),
        "dim_products":  transform_products(raw["ops_products"]),
        "fact_pipeline": transform_pipeline(raw["crm_pipeline"]),
    }
