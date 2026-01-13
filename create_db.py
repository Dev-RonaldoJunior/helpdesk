import sqlite3

# ============================================================
# SCRIPT PARA CRIAR A TABELA "users" NO BANCO SQLITE
# ============================================================
#
# Essa tabela armazena os usuários do sistema Help Desk.
#
# Campos:
# - id: identificador único do usuário
# - username: nome de usuário (obrigatório e único)
# - email: opcional (pode ficar vazio/NULL)
# - senha: senha do usuário (ideal guardar em HASH)
# - is_admin: nível de acesso
#
# Níveis (is_admin):
# 0 = usuário comum
# 1 = atendente
# 2 = admin
#
# ============================================================


# Conecta ao banco SQLite
# Se o arquivo "database.db" não existir, ele será criado automaticamente
conn = sqlite3.connect('database.db')

# Cursor é o objeto usado para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# CRIA A TABELA "users" SE NÃO EXISTIR
# ============================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID único gerado automaticamente

    username TEXT NOT NULL UNIQUE,        -- Nome de usuário obrigatório e único (ex: nome.sobrenome)

    email TEXT,                           -- Email opcional (pode ser NULL)

    senha TEXT NOT NULL,                  -- Senha obrigatória (recomendado salvar em hash)

    is_admin INTEGER NOT NULL             -- Nível do usuário: 0, 1 ou 2
)
""")


# Salva a criação no banco
conn.commit()

# Fecha a conexão
conn.close()


# Mensagem para confirmar que deu certo
print("Tabela de usuários criada com sucesso!")
