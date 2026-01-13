import sqlite3
from werkzeug.security import generate_password_hash

# ============================================================
# SCRIPT PARA CRIAR UM USUÁRIO ATENDENTE COM SENHA CRIPTOGRAFADA
# ============================================================
#
# Esse script serve para garantir que exista um usuário atendente
# no sistema, criando automaticamente caso ele ainda não exista.
#
# Níveis (is_admin):
# 0 = usuário comum
# 1 = atendente
# 2 = admin
#
# ============================================================


# Conecta ao banco de dados SQLite
# Se o arquivo "database.db" não existir, o SQLite cria automaticamente
conn = sqlite3.connect('database.db')

# Cursor é o objeto usado para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# DADOS DO ATENDENTE PADRÃO
# ============================================================
email = 'atendente@atendente.com'

# Cria o hash seguro da senha
# Isso é MUITO melhor do que salvar a senha em texto puro
senha_hash = generate_password_hash('atendente@123')


# ============================================================
# VERIFICA SE O EMAIL JÁ EXISTE NO BANCO
# ============================================================
cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)  # precisa ser tupla, por isso a vírgula no final
)

# fetchone() retorna:
# - (id,) se existir
# - None se não existir
existe = cursor.fetchone()


# ============================================================
# SE NÃO EXISTIR, CRIA O USUÁRIO ATENDENTE
# ============================================================
if not existe:
    cursor.execute(
        "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
        (email, senha_hash, 1)  # 1 = Atendente
    )

    # Salva a alteração no banco
    conn.commit()

    print("Atendente criado com sucesso!")
else:
    # Se já existir, evita duplicação
    print("Atendente já existe!")


# ============================================================
# FECHA A CONEXÃO COM O BANCO
# ============================================================
conn.close()
