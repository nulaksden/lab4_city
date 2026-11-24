import psycopg

DSN = "postgresql://postgres:postgres@localhost:5433/postgres"
CITIES = [
    ("Київ", "01001"),
    ("Львів", "79000"),
    ("Харків", "61000"),
    ("Одеса", "65000"),
    ("Дніпро", "49000"),
    ("Запоріжжя", "69000"),
    ("Вінниця", "21000"),
    ("Полтава", "36000"),
    ("Чернігів", "14000"),
    ("Черкаси", "18000"),
    ("Житомир", "10000"),
    ("Суми", "40000"),
    ("Рівне", "33000"),
    ("Тернопіль", "46000"),
    ("Луцьк", "43000"),
]

with psycopg.connect(DSN) as conn:
    conn.execute("DROP TABLE IF EXISTS districts, cities CASCADE;")
    conn.execute(
        "CREATE TABLE cities (id SERIAL PRIMARY KEY, name TEXT, zip_code TEXT);"
    )
    conn.execute(
        "CREATE TABLE districts (id SERIAL PRIMARY KEY, name TEXT, "
        "city_id INT REFERENCES cities(id) ON DELETE CASCADE);"
    )
    for idx, (city, zip_code) in enumerate(CITIES, start=1):
        conn.execute(
            "INSERT INTO cities (name, zip_code) VALUES (%s, %s);", (city, zip_code)
        )
        for d_num in range(1, 4):
            conn.execute(
                "INSERT INTO districts (name, city_id) VALUES (%s, %s);",
                (f"Район №{d_num} ({city})", idx),
            )

print("Готово! Додано 15 міст і 45 районів (разом 60 записів).")
