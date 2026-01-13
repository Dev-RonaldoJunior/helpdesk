import sqlite3

# ============================================================
# SCRIPT PARA CRIAR UM USUÁRIO ATENDENTE PADRÃO NO BANCO
# ============================================================
#
# Esse script cria um usuário com nível de ATENDENTE caso ele
# ainda não exista no banco de dados.
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

# Cursor é o objeto usado para executar comandos SQL
cursor = conn.cursor()


# ============================================================
# DEFININDO O EMAIL DO ATENDENTE QUE SERÁ CRIADO
# ============================================================
email = 'atendente@atendente.com'


# ============================================================
# VERIFICA SE ESSE EMAIL JÁ EXISTE NO BANCO
# ============================================================
cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)  # precisa ser tupla, por isso a vírgula no final
)

# fetchone() retorna:
# - Uma linha encontrada (ex: (3,))
# - Ou None se não encontrar nada
user = cursor.fetchone()


# ============================================================
# SE NÃO EXISTIR, CRIA O USUÁRIO ATENDENTE
# ============================================================
if not user:
    cursor.execute(
        "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
        (email, 'atendente@123', 1)  # 1 = Atendente
    )

    # Salva a alteração no banco
    conn.commit()

    print("Usuário atendente criado com sucesso!")
else:
    # Se já existir, evita duplicação
    print("Usuário atendente já existe!")


# ============================================================
# FECHA A CONEXÃO COM O BANCO
# ============================================================
conn.close()
