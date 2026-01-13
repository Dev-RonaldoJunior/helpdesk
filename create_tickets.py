import sqlite3

# ============================================================
# SCRIPT PARA CRIAR A TABELA "tickets" (CHAMADOS)
# ============================================================
#
# Esse script cria a tabela "tickets" caso ela ainda não exista.
# Ela guarda os chamados do sistema de Help Desk.
#
# Campos importantes:
#
# status:
# - "Aberto"
# - "Em andamento"
# - "Fechado"
#
# is_hidden (soft delete):
# 0 = visível
# 1 = oculto
#
# hidden_by:
# - guarda o ID do usuário (atendente/admin) que ocultou o chamado
#
# hidden_at:
# - guarda a data/hora em que o chamado foi ocultado
#
# ============================================================


# Conecta ao banco SQLite (database.db)
# Se não existir, ele será criado automaticamente
conn = sqlite3.connect('database.db')

# Cursor usado para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# CRIA A TABELA "tickets" SE NÃO EXISTIR
# ============================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID único do chamado (auto incremento)

    titulo TEXT NOT NULL,                 -- Título do chamado
    descricao TEXT NOT NULL,              -- Descrição do problema

    status TEXT NOT NULL,                 -- Status do ticket: Aberto | Em andamento | Fechado

    user_id INTEGER NOT NULL,             -- ID do usuário que criou o chamado

    attendant_id INTEGER,                 -- ID do atendente responsável (pode ser NULL)

    created_at TEXT NOT NULL,             -- Data/hora de criação do chamado

    started_at TEXT,                      -- Data/hora de início do atendimento (pode ser NULL)
    closed_at TEXT,                       -- Data/hora de fechamento (pode ser NULL)

    is_hidden INTEGER NOT NULL,           -- 0 = visível | 1 = oculto (soft delete)

    hidden_by INTEGER,                    -- ID de quem ocultou (atendente/admin)
    hidden_at TEXT                        -- Data/hora que foi ocultado
)
""")


# Salva a criação no banco
conn.commit()

# Fecha a conexão
conn.close()


# Mensagem para confirmar
print("Tabela de chamados criada com sucesso!")
