import psycopg

try:
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="anp_fuel",
        user="postgres",
        password="123456",
    )
    print("✔ CONEXÃO OK:", conn.execute("SELECT version();").fetchone()[0])
    conn.close()
except Exception as e:
    print("✘ ERRO REAL:", e)
