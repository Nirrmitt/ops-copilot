-- Synthetic PostgreSQL schema. The local beginner seed is app.seed (SQLite).
CREATE TABLE IF NOT EXISTS stores (id INTEGER PRIMARY KEY, name TEXT NOT NULL, region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, price_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, store_id INTEGER REFERENCES stores(id), status TEXT NOT NULL, total_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id), product_id INTEGER REFERENCES products(id), quantity INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS returns (id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id), reason TEXT NOT NULL, status TEXT NOT NULL);
INSERT INTO stores VALUES (1,'North Market','North'),(2,'South Market','South'),(3,'East Market','East'),(4,'West Market','West') ON CONFLICT DO NOTHING;
INSERT INTO products VALUES (1,'Everyday Mug','Home',1299),(2,'Canvas Tote','Accessories',2499),(3,'Trail Bottle','Outdoor',1899),(4,'Desk Lamp','Home',3999),(5,'Wool Scarf','Apparel',4599) ON CONFLICT DO NOTHING;
INSERT INTO orders SELECT n, (n % 4)+1, CASE WHEN n % 5=0 THEN 'processing' ELSE 'shipped' END, 1299+(n%5)*650 FROM generate_series(1,250) AS n ON CONFLICT DO NOTHING;
INSERT INTO order_items SELECT n,n,(n%5)+1,(n%3)+1 FROM generate_series(1,250) AS n ON CONFLICT DO NOTHING;
INSERT INTO returns SELECT n,n,'changed mind','received' FROM generate_series(17,250,17) AS n ON CONFLICT DO NOTHING;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ops_reader') THEN CREATE ROLE ops_reader LOGIN PASSWORD 'change-me'; END IF;
END $$;
GRANT CONNECT ON DATABASE ops TO ops_reader;
GRANT USAGE ON SCHEMA public TO ops_reader;
GRANT SELECT ON stores, products, orders, order_items, returns TO ops_reader;
