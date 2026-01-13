import sqlite3

# ============================================================
# SCRIPT PARA CRIAR UM USUÁRIO ADMIN PADRÃO NO BANCO DE DADOS
# ============================================================
#
# Esse script serve para garantir que exista um usuário ADMIN
# no seu sistema, criando automaticamente caso não exista.
#
# Níveis de acesso (is_admin):
# 0 = Usuário comum
# 1 = Atendente
# 2 = Admin
#
# ============================================================


# Conecta ao banco de dados SQLite
# Se o arquivo "database.db" não existir, o SQLite cria automaticamente
conn = sqlite3.connect('database.db')

# Cria um cursor, que é o "controle" para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# VERIFICA SE JÁ EXISTE UM USUÁRIO COM ESSE EMAIL
# ============================================================
cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    ('admin@admin.com',)  # IMPORTANTE: precisa ser tupla, por isso a vírgula no final
)

# fetchone() retorna:
# - Uma linha encontrada (ex: (1,))
# - Ou None se não encontrar nada
user = cursor.fetchone()


# ============================================================
# SE NÃO EXISTIR, CRIA O ADMIN
# ============================================================
if not user:
    cursor.execute(
        "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
        ('admin@admin.com', 'admin@123', 2)  # 2 = Admin
    )

    # Salva a alteração no banco
    conn.commit()

    print("Admin criado com sucesso!")
else:
    # Se já existe, não cria de novo
    print("Admin já existe!")


# ============================================================
# FECHA A CONEXÃO COM O BANCO
# ============================================================
conn.close()
