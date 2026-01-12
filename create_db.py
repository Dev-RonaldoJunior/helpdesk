import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    senha TEXT NOT NULL,
    is_admin INTEGER NOT NULL
)
""")

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")
