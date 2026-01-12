import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
    ('admin@admin.com', 'admin123', 1)
)

conn.commit()
conn.close()
exit()
