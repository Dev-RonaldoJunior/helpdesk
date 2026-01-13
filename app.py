# ============================================================
# IMPORTAÇÕES
# ============================================================

# Flask:
# - Flask: cria a aplicação
# - render_template: renderiza páginas HTML (templates)
# - request: pega dados enviados por formulários (POST)
# - redirect: redireciona para outra rota
# - url_for: gera URLs de rotas pelo nome da função
# - session: guarda informações do usuário logado
from flask import Flask, render_template, request, redirect, url_for, session

# SQLite: banco de dados simples em arquivo (.db)
import sqlite3

# datetime: para salvar datas de criação/início/fechamento do ticket
from datetime import datetime

# Werkzeug Security:
# - generate_password_hash: cria um hash seguro da senha
# - check_password_hash: compara senha digitada com o hash do banco
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

# Cria a aplicação Flask
app = Flask(__name__)

# Chave secreta usada para criptografar/assinar a session
# IMPORTANTE: em produção use algo forte e escondido (env var)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# FUNÇÃO DE CONEXÃO COM O BANCO
# ============================================================

def get_db_connection():
    """
    Abre uma conexão com o banco de dados SQLite.
    Toda vez que você precisar executar SQL, use essa função.
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
    - GET: mostra a página login.html
    - POST: valida email e senha (hash) e faz login
    """

    # Se o usuário enviou o formulário
    if request.method == 'POST':
        # Pega os dados digitados no formulário
        email = request.form['email']
        senha = request.form['senha']

        # Conecta ao banco
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca o usuário pelo email
        # (Agora não buscamos por senha aqui, porque a senha está em hash)
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        # Retorna a primeira linha encontrada ou None
        user = cursor.fetchone()
        conn.close()

        # Se encontrou o usuário, valida a senha
        if user:
            # user[2] = coluna "senha" no banco
            # agora é um hash (não é mais a senha pura)
            senha_hash = user[2]

            # check_password_hash compara a senha digitada com o hash do banco
            if check_password_hash(senha_hash, senha):
                # Salva informações do usuário logado na sessão
                session['user_id'] = user[0]  # ID do usuário
                session['nivel'] = user[3]    # nível de acesso (0,1,2)

                # Redireciona para o dashboard
                return redirect(url_for('dashboard'))

        # Se não achou usuário ou senha não bateu
        return "Email ou senha inválidos!"

    # Se for GET, apenas mostra a tela de login
    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    """
    Limpa a sessão e volta para o login.
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
    - GET: mostra register.html
    - POST: cria usuário com senha criptografada (hash)
    """

    if request.method == 'POST':
        # Dados do formulário
        email = request.form['email']
        senha = request.form['senha']

        # Gera hash da senha
        # Isso impede que a senha fique salva em texto puro no banco
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insere o usuário no banco
        # is_admin = 0 (usuário comum)
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
    - Mostra os tickets de acordo com o nível do usuário
    - Admin (nível 2) vê tudo, inclusive ocultos
    - Usuário e atendente não veem ocultos
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ADMIN vê tudo (inclusive ocultos)
    if session.get('nivel') == 2:
        cursor.execute("""
            SELECT
                tickets.id,
                tickets.titulo,
                tickets.descricao,
                tickets.status,
                tickets.created_at,
                tickets.started_at,
                tickets.closed_at,
                creator.email,
                attendant.email
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        """)
    else:
        # Usuário e atendente não veem ocultos
        # Regras:
        # - tickets.is_hidden = 0 => só visíveis
        # - usuário comum (nível 0) vê só os próprios tickets
        # - atendente (nível 1) vê todos os tickets visíveis
        cursor.execute("""
            SELECT
                tickets.id,
                tickets.titulo,
                tickets.descricao,
                tickets.status,
                tickets.created_at,
                tickets.started_at,
                tickets.closed_at,
                creator.email,
                attendant.email
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            WHERE tickets.is_hidden = 0
              AND (tickets.user_id = ? OR ? IN (1))
        """, (session['user_id'], session.get('nivel')))

    # Pega todos os tickets retornados
    tickets = cursor.fetchall()
    conn.close()

    # Renderiza a página e envia a lista de tickets
    return render_template('dashboard.html', tickets=tickets)


# ============================================================
# CRIAR TICKET
# ============================================================

@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    """
    Criação de ticket:
    - GET: mostra o formulário
    - POST: salva o ticket no banco como "Aberto"
    """

    # Só logado pode criar ticket
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Se enviou o formulário
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insere o ticket no banco
        cursor.execute("""
            INSERT INTO tickets
            (titulo, descricao, status, user_id, created_at, is_hidden)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            descricao,
            'Aberto',  # status inicial
            session['user_id'],  # criador do chamado
            datetime.now().strftime('%d/%m/%Y %H:%M'),  # data/hora atual
            0  # is_hidden = 0 => visível
        ))

        conn.commit()
        conn.close()

        # Volta pro dashboard
        return redirect(url_for('dashboard'))

    # Se for GET, mostra a página
    return render_template('create_ticket.html')


# ============================================================
# INICIAR ATENDIMENTO DO TICKET
# ============================================================

@app.route('/start-ticket/<int:ticket_id>')
def start_ticket(ticket_id):
    """
    Inicia atendimento:
    - Somente atendente (1) ou admin (2)
    - Só inicia se estiver 'Aberto'
    - Define attendant_id e started_at
    """

    # Se não for atendente nem admin, bloqueia
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
        session['user_id'],  # quem iniciou atendimento
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        ticket_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# FECHAR TICKET
# ============================================================

@app.route('/close-ticket/<int:ticket_id>')
def close_ticket(ticket_id):
    """
    Fecha o ticket:
    - Somente atendente (1) ou admin (2)
    - Só fecha se estiver 'Em andamento'
    - Salva closed_at
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
# OCULTAR TICKET (SOFT DELETE)
# ============================================================

@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
    """
    Oculta um ticket (soft delete):
    - Não apaga do banco
    - Apenas marca is_hidden = 1
    - Somente atendente (1) ou admin (2)
    """

    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tickets SET is_hidden = 1 WHERE id = ?",
        (ticket_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# INICIAR O SERVIDOR
# ============================================================

if __name__ == '__main__':
    # debug=True:
    # - reinicia o servidor automaticamente quando você altera o código
    # - mostra erros detalhados no navegador
    app.run(debug=True)
