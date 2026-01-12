import sqlite3
# is_admin: 0 = usuário | 1 = atendente | 2 = admin

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

email = 'atendente@atendente.com'

cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)
)

if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
        (email, 'atendente@123', 1)
    )
    conn.commit()
    print("Usuário atendente criado com sucesso!")
else:
    print("Usuário atendente já existe!")

conn.close()
