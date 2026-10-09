"""Create a local deterministic SQLite dataset for beginner setup and CI."""
from pathlib import Path

from sqlalchemy import create_engine, text

DB = Path(__file__).resolve().parents[1] / "data" / "ops.db"


def seed() -> None:
    """Rebuild a few hundred synthetic retail rows."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB}")
    with engine.begin() as conn:
        for table in ("order_items", "returns", "orders", "products", "stores"):
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.execute(text("CREATE TABLE stores (id INTEGER PRIMARY KEY, name TEXT, region TEXT)"))
        conn.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price_cents INTEGER)"))
        conn.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY, store_id INTEGER, status TEXT, total_cents INTEGER)"))
        conn.execute(text("CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER)"))
        conn.execute(text("CREATE TABLE returns (id INTEGER PRIMARY KEY, order_id INTEGER, reason TEXT, status TEXT)"))
        conn.execute(text("INSERT INTO stores VALUES (1,'North Market','North'),(2,'South Market','South'),(3,'East Market','East'),(4,'West Market','West')"))
        conn.execute(text("INSERT INTO products VALUES (1,'Everyday Mug','Home',1299),(2,'Canvas Tote','Accessories',2499),(3,'Trail Bottle','Outdoor',1899),(4,'Desk Lamp','Home',3999),(5,'Wool Scarf','Apparel',4599)"))
        for i in range(1, 251):
            store = (i % 4) + 1; status = "shipped" if i % 5 else "processing"
            amount = 1299 + (i % 5) * 650
            conn.execute(text("INSERT INTO orders VALUES (:i,:s,:st,:a)"), {"i": i, "s": store, "st": status, "a": amount})
            conn.execute(text("INSERT INTO order_items VALUES (:i,:o,:p,:q)"), {"i": i, "o": i, "p": (i % 5) + 1, "q": 1 + (i % 3)})
            if i % 17 == 0:
                conn.execute(text("INSERT INTO returns VALUES (:i,:o,'changed mind','received')"), {"i": i, "o": i})
    print(f"Seeded {DB}")


if __name__ == "__main__":
    seed()
