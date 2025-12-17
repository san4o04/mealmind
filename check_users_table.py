from dotenv import load_dotenv
load_dotenv()

import os
import psycopg
from urllib.parse import urlparse

u = os.getenv("DATABASE_URL")
print("DATABASE_URL =", u)

p = urlparse(u)

conn = psycopg.connect(
    dbname=p.path[1:],
    user=p.username,
    password=p.password,
    host=p.hostname,
    port=p.port or 5432,
)

cur = conn.cursor()

print("\n=== users columns ===")
cur.execute("""
select column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'users'
order by ordinal_position
""")
print(cur.fetchall())

print("\n=== tables named users ===")
cur.execute("""
select table_schema, table_name
from information_schema.tables
where table_name = 'users'
""")
print(cur.fetchall())

print("\n=== search_path ===")
cur.execute("show search_path")
print(cur.fetchall())

conn.close()
