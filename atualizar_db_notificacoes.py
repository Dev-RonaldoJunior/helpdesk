import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

def add_column(table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✅ Coluna adicionada: {table}.{column}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"ℹ️ Já existe: {table}.{column}")
        else:
            print(f"❌ Erro ao adicionar {table}.{column}: {e}")

# ==============================
# NOTIFICAÇÕES POR PERFIL (SEEN)
# ==============================
add_column("tickets", "user_seen_comment_id", "INTEGER")
add_column("tickets", "attendant_seen_comment_id", "INTEGER")
add_column("tickets", "admin_seen_comment_id", "INTEGER")

add_column("tickets", "user_seen_status_at", "TEXT")
add_column("tickets", "attendant_seen_status_at", "TEXT")
add_column("tickets", "admin_seen_status_at", "TEXT")

conn.commit()
conn.close()

print("\n✅ Banco atualizado com sucesso!")
