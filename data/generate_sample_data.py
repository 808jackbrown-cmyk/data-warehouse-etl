import random, sqlite3, string
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

DB_PATH = Path(__file__).parent / "sample.db"
CRM_PATH = Path(__file__).parent / "crm"
CRM_PATH.mkdir(exist_ok=True)

N_ACCOUNTS, N_CONTACTS, N_PRODUCTS, N_ORDERS = 2000, 4500, 150, 25000

INDUSTRIES = ["Technology","Healthcare","Financial Services","Manufacturing","Retail","Real Estate","Construction","Logistics","Education","Energy"]
STATES = ["CA","TX","FL","NY","IL","OH","GA","NC","MI","WA","IN","TN","AZ","CO","MN"]
CATEGORIES = {"Software":["CRM","ERP","Analytics","Security"],"Services":["Implementation","Training","Support"],"Hardware":["Servers","Networking","Endpoints"]}

def rand_date(start, end=0):
    return datetime.now() - timedelta(days=random.randint(end, start))

def rand_id(p, n=8):
    return p + "".join(random.choices(string.digits, k=n))

print("Generating accounts...")
rev = np.clip(np.random.lognormal(12.5, 2.0, N_ACCOUNTS), 10000, 50000000)
accounts = pd.DataFrame([{"account_id": rand_id("ACC"), "account_name": f"Corp{i:04d} Inc", "industry": random.choice(INDUSTRIES), "annual_revenue": round(rev[i],2), "billing_state": random.choice(STATES), "billing_country": "US", "created_date": rand_date(1460,30).isoformat(), "updated_at": rand_date(200).isoformat()} for i in range(N_ACCOUNTS)])
accounts.to_csv(CRM_PATH / "accounts.csv", index=False)
print(f"  {len(accounts):,} accounts")

account_ids = accounts["account_id"].tolist()

print("Generating contacts...")
fnames = ["James","Maria","David","Sarah","Michael","Ashley","Robert","Jennifer","DJ","Alex"]
lnames = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Taylor","Anderson"]
contacts = pd.DataFrame([{"contact_id": rand_id("CON"), "account_id": random.choice(account_ids), "first_name": random.choice(fnames), "last_name": random.choice(lnames), "email": f"user{i}@company{random.randint(1,500)}.com", "phone": str(random.randint(2000000000,9999999999)), "title": "Manager", "updated_at": rand_date(730).isoformat()} for i in range(N_CONTACTS)])
contacts.to_csv(CRM_PATH / "contacts.csv", index=False)
print(f"  {len(contacts):,} contacts")

print("Generating opportunities...")
stages = ["Prospecting","Qualification","Proposal","Negotiation","Closed Won","Closed Lost"]
opps = pd.DataFrame([{"opp_id": rand_id("OPP"), "account_id": random.choice(account_ids), "stage_name": random.choice(stages), "amount": round(random.uniform(5000,2000000),2), "close_date": rand_date(730,30).isoformat(), "created_date": rand_date(730,90).isoformat(), "updated_at": rand_date(90).isoformat()} for _ in range(3000)])
opps.to_csv(CRM_PATH / "opportunities.csv", index=False)
print(f"  {len(opps):,} opportunities")

print("Generating products...")
prods = []
for cat, subs in CATEGORIES.items():
    for sub in subs:
        for i in range(12):
            cost = round(random.uniform(100,50000),2)
            prods.append({"product_id": rand_id("PRD"), "sku": f"{cat[:3].upper()}-{sub[:3].upper()}-{i:03d}", "product_name": f"{sub} {cat} v{i+1}", "category": cat, "sub_category": sub, "unit_cost": cost, "unit_price": round(cost*random.uniform(1.3,3.5),2), "status": "active", "updated_at": rand_date(365).isoformat()})
products = pd.DataFrame(prods)
product_ids = products["product_id"].tolist()
print(f"  {len(products):,} products")

print("Generating orders and lines...")
orders, lines = [], []
for _ in range(N_ORDERS):
    oid = rand_id("ORD")
    odate = rand_date(730,1)
    orders.append({"order_id": oid, "customer_id": random.choice(account_ids), "rep_id": rand_id("REP",4), "order_date": odate.isoformat(), "ship_date": (odate+timedelta(days=random.randint(1,14))).isoformat(), "status": "shipped", "updated_at": rand_date(30).isoformat()})
    for _ in range(random.randint(1,5)):
        qty = random.randint(1,50)
        lines.append({"line_id": rand_id("LIN"), "order_id": oid, "product_id": random.choice(product_ids), "quantity": qty, "unit_price": round(random.uniform(100,10000),2), "unit_cost": round(random.uniform(50,5000),2), "created_at": odate.isoformat()})
orders_df = pd.DataFrame(orders)
lines_df = pd.DataFrame(lines)
print(f"  {len(orders_df):,} orders, {len(lines_df):,} lines")

print("Generating invoices...")
sample_oids = random.sample(orders_df["order_id"].tolist(), min(22000, len(orders_df)))
invoices = []
for oid in sample_oids:
    inv_date = rand_date(700,1)
    amt = round(random.uniform(500,500000),2)
    paid = round(amt * random.random(),2)
    invoices.append({"invoice_id": rand_id("INV"), "order_id": oid, "invoice_date": inv_date.isoformat(), "due_date": (inv_date+timedelta(days=30)).isoformat(), "invoice_amount": amt, "amount_paid": paid, "paid_date": rand_date(60).isoformat() if paid >= amt*0.9 else None, "updated_at": rand_date(30).isoformat()})
invoices_df = pd.DataFrame(invoices)
print(f"  {len(invoices_df):,} invoices")

print("\nWriting to SQLite...")
conn = sqlite3.connect(DB_PATH)
for name, df in [("raw_orders",orders_df),("raw_order_lines",lines_df),("raw_products",products),("raw_invoices",invoices_df)]:
    df.to_sql(name, conn, if_exists="replace", index=False)
    print(f"  {name}: {len(df):,} rows")
conn.close()

total = len(accounts)+len(contacts)+len(opps)+len(products)+len(orders_df)+len(lines_df)+len(invoices_df)
print(f"\nDone. Total records: {total:,}")
