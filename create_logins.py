import sqlite3
from werkzeug.security import generate_password_hash

# ============================================================
# SCRIPT ÚNICO PARA CRIAR USUÁRIOS PADRÃO (COM RESUMO + LISTAS)
# ============================================================
#
# Cria automaticamente:
# - admin.master         (nível 2)
# - atendente.suporte    (nível 1)
# - atendente2.suporte   (nível 1)
# - usuario.teste        (nível 0)
# - usuario2.teste       (nível 0)
#
# Regras:
# - Se já existir, não cria novamente
# - Salva senha com HASH
#
# Níveis (is_admin):
# 0 = usuário comum
# 1 = atendente
# 2 = admin
#
# No final mostra:
# - Total de criados
# - Total que já existiam
# - Lista dos usernames criados
# - Lista dos usernames já existentes
#
# ============================================================


# ============================================================
# LISTA DE USUÁRIOS PARA CRIAR
# ============================================================
usuarios_para_criar = [
    {"username": "admin.master",       "senha": "admin@123",      "nivel": 2},
    {"username": "atendente.suporte",  "senha": "atendente@123",  "nivel": 1},
    {"username": "atendente2.suporte", "senha": "atendente@123",  "nivel": 1},
    {"username": "usuario.teste",      "senha": "usuario@123",    "nivel": 0},
    {"username": "usuario2.teste",     "senha": "usuario@123",    "nivel": 0},
]


# ============================================================
# CONTADORES E LISTAS PARA O RESUMO FINAL
# ============================================================
criados = 0
ja_existiam = 0

usuarios_criados = []
usuarios_ja_existiam = []


# ============================================================
# CONECTA NO BANCO
# ============================================================
conn = sqlite3.connect('database.db')
cursor = conn.cursor()


# ============================================================
# FUNÇÃO PARA CRIAR USUÁRIO SE NÃO EXISTIR
# ============================================================
def criar_usuario(username, senha, nivel):
    """
    Cria um usuário no banco se ele ainda não existir.

    Atualiza:
    - contadores (criados / ja_existiam)
    - listas (usuarios_criados / usuarios_ja_existiam)
    """

    global criados, ja_existiam
    global usuarios_criados, usuarios_ja_existiam

    # Verifica se o username já existe
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existe = cursor.fetchone()

    # Se não existir, cria o usuário
    if not existe:
        # Gera hash seguro da senha
        senha_hash = generate_password_hash(senha)

        # Insere no banco
        cursor.execute(
            "INSERT INTO users (username, email, senha, is_admin) VALUES (?, ?, ?, ?)",
            (username, None, senha_hash, nivel)
        )

        # Confirma alteração no banco
        conn.commit()

        # Atualiza contadores/listas
        criados += 1
        usuarios_criados.append(username)

        print(f"✅ Usuário criado: {username} (nível {nivel})")

    else:
        # Se já existir, apenas registra
        ja_existiam += 1
        usuarios_ja_existiam.append(username)

        print(f"⚠️ Usuário já existe: {username}")


# ============================================================
# CRIA TODOS OS USUÁRIOS DA LISTA
# ============================================================
for u in usuarios_para_criar:
    criar_usuario(u["username"], u["senha"], u["nivel"])


# ============================================================
# FECHA O BANCO
# ============================================================
conn.close()


# ============================================================
# RESUMO FINAL
# ============================================================
print("\n==================== RESUMO FINAL ====================")
print(f"✅ Criados: {criados} | ⚠️ Já existiam: {ja_existiam}")
print("======================================================\n")


# Lista de criados
print("📌 Usuários CRIADOS:")
if usuarios_criados:
    for username in usuarios_criados:
        print(f" - {username}")
else:
    print(" - Nenhum (todos já existiam)")


# Lista de já existentes
print("\n📌 Usuários que JÁ EXISTIAM:")
if usuarios_ja_existiam:
    for username in usuarios_ja_existiam:
        print(f" - {username}")
else:
    print(" - Nenhum (todos foram criados agora)")

print("\n🎉 Processo finalizado!")
