# ============================================================
# IMPORTAÇÕES
# ============================================================

# Flask:
# - Flask: cria a aplicação
# - render_template: renderiza HTML dentro da pasta /templates
# - request: pega dados do formulário (POST)
# - redirect: redireciona para outra rota
# - url_for: cria links para rotas usando o nome da função
# - session: armazena dados do usuário logado (id, nível, etc)
from flask import Flask, render_template, request, redirect, url_for, session

# SQLite (banco de dados em arquivo)
import sqlite3

# Para registrar data e hora dos eventos do chamado
from datetime import datetime

# Segurança:
# - generate_password_hash: gera hash da senha no cadastro
# - check_password_hash: valida a senha digitada com o hash salvo
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

# Cria o app Flask
app = Flask(__name__)

# Chave secreta usada para sessão (session)
# Em produção: usar uma chave forte e escondida (variável de ambiente)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# FUNÇÃO DE CONEXÃO COM O BANCO
# ============================================================

def get_db_connection():
    """
    Abre uma conexão com o banco SQLite.
    Sempre que precisar consultar ou alterar o banco, use essa função.
    """
    conn = sqlite3.connect('database.db')
    return conn


# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota de login:
    - GET: exibe a página login.html
    - POST: valida email e senha (hash) e faz login
    """

    if request.method == 'POST':
        # Pega dados do formulário
        email = request.form['email']
        senha = request.form['senha']

        # Conecta ao banco
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca o usuário pelo email
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        # Retorna o usuário encontrado (ou None)
        user = cursor.fetchone()
        conn.close()

        # Se o usuário existe, valida a senha
        if user:
            # user[2] é a coluna senha (hash)
            senha_hash = user[2]

            # Verifica se a senha digitada bate com o hash salvo
            if check_password_hash(senha_hash, senha):
                # Guarda dados na sessão
                session['user_id'] = user[0]  # ID do usuário
                session['nivel'] = user[3]    # nível (0/1/2)

                # Vai pro dashboard
                return redirect(url_for('dashboard'))

        # Caso não encontre usuário ou senha esteja errada
        return "Email ou senha inválidos!"

    # Se for GET, apenas renderiza o HTML de login
    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    """
    Limpa os dados da sessão e volta pro login.
    """
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# REGISTER (CADASTRO)
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Cadastro de usuário:
    - GET: exibe register.html
    - POST: cria usuário com senha em hash
    """

    if request.method == 'POST':
        # Dados do formulário
        email = request.form['email']
        senha = request.form['senha']

        # Cria hash seguro da senha
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insere usuário como nível 0 (usuário comum)
        cursor.execute(
            "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
            (email, senha_hash, 0)
        )

        conn.commit()
        conn.close()

        return "Usuário cadastrado com sucesso!"

    return render_template('register.html')


# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
def dashboard():
    """
    Dashboard:
    - Admin vê todos os chamados (inclusive ocultos)
    - Usuário comum vê somente os próprios chamados (visíveis)
    - Atendente vê chamados visíveis que estão:
        - Abertos
        - OU que ele mesmo está atendendo (attendant_id = ele)
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ============================================================
    # ADMIN (nível 2) vê tudo
    # ============================================================
    if session.get('nivel') == 2:
        cursor.execute("""
            SELECT
                tickets.id,          -- ticket[0]
                tickets.titulo,       -- ticket[1]
                tickets.descricao,    -- ticket[2]
                tickets.status,       -- ticket[3]
                tickets.created_at,   -- ticket[4]
                tickets.started_at,   -- ticket[5]
                tickets.closed_at,    -- ticket[6]
                tickets.is_hidden,    -- ticket[7]
                creator.email,        -- ticket[8]
                attendant.email,      -- ticket[9]
                hider.email,          -- ticket[10] (quem ocultou)
                tickets.hidden_at     -- ticket[11] (quando ocultou)
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        """)

    # ============================================================
    # USUÁRIO COMUM (nível 0) vê só os próprios tickets visíveis
    # ============================================================
    else:
        if session.get('nivel') == 0:
            cursor.execute("""
                SELECT
                    tickets.id,
                    tickets.titulo,
                    tickets.descricao,
                    tickets.status,
                    tickets.created_at,
                    tickets.started_at,
                    tickets.closed_at,
                    tickets.is_hidden,
                    creator.email,
                    attendant.email,
                    hider.email,
                    tickets.hidden_at
                FROM tickets
                JOIN users AS creator ON tickets.user_id = creator.id
                LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
                LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
                WHERE tickets.is_hidden = 0
                  AND tickets.user_id = ?
            """, (session['user_id'],))

        # ============================================================
        # ATENDENTE (nível 1)
        # vê chamados visíveis que:
        # - estão "Aberto"
        # - OU são dele (attendant_id = ele)
        # ============================================================
        elif session.get('nivel') == 1:
            cursor.execute("""
                SELECT
                    tickets.id,
                    tickets.titulo,
                    tickets.descricao,
                    tickets.status,
                    tickets.created_at,
                    tickets.started_at,
                    tickets.closed_at,
                    tickets.is_hidden,
                    creator.email,
                    attendant.email,
                    hider.email,
                    tickets.hidden_at
                FROM tickets
                JOIN users AS creator ON tickets.user_id = creator.id
                LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
                LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
                WHERE tickets.is_hidden = 0
                  AND (
                        tickets.status = 'Aberto'
                        OR tickets.attendant_id = ?
                      )
            """, (session['user_id'],))

    # Pega todos os tickets retornados
    tickets = cursor.fetchall()
    conn.close()

    # Envia os tickets para o HTML
    return render_template('dashboard.html', tickets=tickets)


# ============================================================
# CRIAR CHAMADO
# ============================================================

@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    """
    Criação de ticket:
    - GET: mostra formulário
    - POST: cria ticket no banco como "Aberto"
    """

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tickets
            (titulo, descricao, status, user_id, created_at, is_hidden)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            descricao,
            'Aberto',  # status inicial
            session['user_id'],
            datetime.now().strftime('%d/%m/%Y %H:%M'),
            0  # visível
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('create_ticket.html')


# ============================================================
# INICIAR ATENDIMENTO
# ============================================================

@app.route('/start-ticket/<int:ticket_id>')
def start_ticket(ticket_id):
    """
    Inicia atendimento:
    - Somente atendente (1) ou admin (2)
    - Só inicia se o ticket estiver "Aberto"
    """

    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?, attendant_id = ?, started_at = ?
        WHERE id = ? AND status = 'Aberto'
    """, (
        'Em andamento',
        session['user_id'],  # atendente que pegou o ticket
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        ticket_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# FECHAR CHAMADO
# ============================================================

@app.route('/close-ticket/<int:ticket_id>')
def close_ticket(ticket_id):
    """
    Fecha o ticket:
    - Somente atendente (1) ou admin (2)
    - Só fecha se estiver "Em andamento"
    """

    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?, closed_at = ?
        WHERE id = ? AND status = 'Em andamento'
    """, (
        'Fechado',
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        ticket_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# OCULTAR CHAMADO (SOFT DELETE + REGISTRO DE QUEM OCULTOU)
# ============================================================

@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
    """
    Oculta o ticket:
    - Não apaga do banco
    - Marca is_hidden = 1
    - Salva hidden_by e hidden_at
    - Somente atendente (1) ou admin (2)
    """

    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET is_hidden = 1,
            hidden_by = ?,
            hidden_at = ?
        WHERE id = ?
    """, (
        session['user_id'],  # quem ocultou
        datetime.now().strftime('%d/%m/%Y %H:%M'),  # quando ocultou
        ticket_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# DESOCULTAR CHAMADO (SOMENTE ADMIN)
# ============================================================

@app.route('/unhide-ticket/<int:ticket_id>')
def unhide_ticket(ticket_id):
    """
    Desoculta o ticket:
    - Somente admin (nível 2)
    - Volta is_hidden para 0
    - Remove hidden_by e hidden_at
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Se não for admin, bloqueia
    if session.get('nivel') != 2:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET is_hidden = 0,
            hidden_by = NULL,
            hidden_at = NULL
        WHERE id = ?
    """, (ticket_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# INICIAR O SERVIDOR
# ============================================================

if __name__ == '__main__':
    # debug=True:
    # - reinicia sozinho quando você salva
    # - mostra erros detalhados no navegador
    app.run(debug=True)
