import sqlite3

# ============================================================
# SCRIPT PARA CRIAR A TABELA "users" NO BANCO SQLITE
# ============================================================
#
# Esse script cria a tabela "users" caso ela ainda não exista.
# Ela armazena os usuários do sistema e o nível de permissão.
#
# Níveis de acesso (is_admin):
# 0 = Usuário comum
# 1 = Atendente
# 2 = Admin
#
# ============================================================


# Conecta ao banco SQLite
# Se o arquivo "database.db" não existir, ele será criado automaticamente
conn = sqlite3.connect('database.db')

# Cursor é o objeto usado para executar comandos SQL no banco
cursor = conn.cursor()


# ============================================================
# CRIAÇÃO DA TABELA "users" (SE NÃO EXISTIR)
# ============================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID único gerado automaticamente
    email TEXT NOT NULL,                  -- Email do usuário (obrigatório)
    senha TEXT NOT NULL,                  -- Senha do usuário (obrigatória)
    is_admin INTEGER NOT NULL             -- Nível do usuário (0, 1 ou 2)
)
""")


# Salva a criação da tabela no banco
conn.commit()

# Fecha a conexão com o banco
conn.close()


# Mensagem no terminal para confirmar que deu certo
print("Tabela de usuários criada com sucesso!")
