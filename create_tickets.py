import sqlite3

# ============================================================
# SCRIPT PARA CRIAR A TABELA "tickets" NO BANCO SQLITE
# ============================================================
#
# Essa tabela guarda os chamados (tickets) do sistema.
#
# Campos principais:
# - titulo / descricao: informações do chamado
# - status: controla o andamento do ticket
# - user_id: quem criou o chamado
# - attendant_id: quem está atendendo (ou atendeu)
# - created_at / started_at / closed_at: datas do ciclo do ticket
# - is_hidden: serve como "soft delete" (ocultar sem apagar)
#
# Regras:
# status:
# - "Aberto"
# - "Em andamento"
# - "Fechado"
#
# is_hidden:
# 0 = visível
# 1 = oculto
#
# ============================================================


# Conecta ao banco de dados SQLite
# Se o arquivo "database.db" não existir, ele será criado automaticamente
conn = sqlite3.connect('database.db')

# Cursor é o objeto usado para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# CRIA A TABELA "tickets" CASO AINDA NÃO EXISTA
# ============================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID único gerado automaticamente

    titulo TEXT NOT NULL,                 -- Título do chamado (obrigatório)
    descricao TEXT NOT NULL,              -- Descrição do chamado (obrigatória)

    status TEXT NOT NULL,                 -- Status do chamado (Aberto, Em andamento, Fechado)

    user_id INTEGER NOT NULL,             -- ID do usuário que criou o ticket

    attendant_id INTEGER,                 -- ID do atendente responsável (pode ser NULL)

    created_at TEXT NOT NULL,             -- Data/hora de criação do chamado (obrigatório)
    started_at TEXT,                      -- Data/hora que começou o atendimento (pode ser NULL)
    closed_at TEXT,                       -- Data/hora que foi fechado (pode ser NULL)

    is_hidden INTEGER NOT NULL            -- 0 = visível | 1 = oculto
)
""")


# Salva as alterações (criação da tabela)
conn.commit()

# Fecha a conexão com o banco
conn.close()


# Mensagem no terminal confirmando que deu certo
print("Tabela de chamados criada com sucesso!")
