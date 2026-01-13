import sqlite3
from werkzeug.security import generate_password_hash

# ============================================================
# SCRIPT PARA CRIAR UM ADMIN PADRÃO COM SENHA CRIPTOGRAFADA
# ============================================================
#
# Esse script:
# 1) Conecta no banco SQLite (database.db)
# 2) Verifica se já existe um usuário com o email definido
# 3) Se não existir, cria o admin com senha em HASH
#
# Níveis (is_admin):
# 0 = usuário
# 1 = atendente
# 2 = admin
#
# ============================================================


# Conecta ao banco de dados SQLite
conn = sqlite3.connect('database.db')

# Cursor para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# DADOS DO ADMIN PADRÃO
# ============================================================
email = 'admin@admin.com'

# Gera um hash seguro para a senha
# Isso evita salvar a senha em texto puro no banco (mais seguro)
senha_hash = generate_password_hash('admin@123')


# ============================================================
# VERIFICA SE O ADMIN JÁ EXISTE NO BANCO
# ============================================================
cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)
)

# fetchone() retorna:
# - (id,) se encontrar
# - None se não existir
existe = cursor.fetchone()


# ============================================================
# SE NÃO EXISTIR, CRIA O ADMIN
# ============================================================
if not existe:
    cursor.execute(
        "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
        (email, senha_hash, 2)  # 2 = Admin
    )

    # Salva as alterações no banco
    conn.commit()

    print("Admin criado com sucesso!")
else:
    # Se já existe, não cria novamente
    print("Admin já existe!")


# ============================================================
# FECHA A CONEXÃO COM O BANCO
# ============================================================
conn.close()
