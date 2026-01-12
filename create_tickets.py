import sqlite3

# status: Aberto | Em andamento | Fechado
# is_hidden: 0 = visível | 1 = oculto

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    status TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    attendant_id INTEGER,
    created_at TEXT NOT NULL,
    started_at TEXT,
    closed_at TEXT,
    is_hidden INTEGER NOT NULL
)
""")

conn.commit()
conn.close()

print("Tabela de chamados criada com sucesso!")
