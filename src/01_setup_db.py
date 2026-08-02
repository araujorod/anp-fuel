import psycopg
from psycopg import sql

# conecta no database administrativo "postgres", que sempre existe
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="postgres",  # <- aqui está o truque
    user="postgres",
    password="123456",
    autocommit=True,  # CREATE DATABASE não pode rodar dentro de transação
)

# verifica se o database já existe antes de criar
existe = conn.execute(
    "SELECT 1 FROM pg_database WHERE datname = %s", ("anp_fuel",)
).fetchone()

if existe:
    print("Database anp_fuel já existe — nada a fazer.")
else:
    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("anp_fuel")))
    print("✔ Database anp_fuel criado.")

conn.close()
