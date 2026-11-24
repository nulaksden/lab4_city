import psycopg

with psycopg.connect("postgresql://postgres:postgres@localhost:5433/postgres") as conn:
    conn.execute("ALTER DATABASE postgres SET timezone TO 'UTC';")

print("Часовий пояс бази виправлено!")
