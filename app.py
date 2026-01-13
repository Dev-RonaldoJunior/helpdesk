# ============================================================
# IMPORTAÇÕES
# ============================================================

# Importa os recursos principais do Flask
from flask import Flask, render_template, request, redirect, url_for, session

# SQLite (banco de dados em arquivo)
import sqlite3

# Para salvar data/hora de criação, início e fechamento do ticket
from datetime import datetime

# Para criptografar senha (hash) e validar senha no login
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

# Cria o app Flask
app = Flask(__name__)

# Chave secreta para assinar/criptografar os dados da sessão
# IMPORTANTE: em produção isso deve ser forte e escondido (variável de ambiente)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# FUNÇÃO PARA CONECTAR NO BANCO
# ============================================================

def get_db_connection():
    """
    Abre uma conexão com o banco SQLite.
    Sempre que precisar consultar ou alterar dados, use essa função.
    """
    conn = sqlite3.connect('database.db')
    return conn


# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Tela de login:
    - GET: mostra a página login.html
    - POST: valida email e senha usando hash
    """

    # Se o formulário foi enviado
    if request.method == 'POST':
        # Captura os dados enviados pelo formulário
        email = request.form['email']
        senha = request.form['senha']

        # Conecta no banco
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca o usuário pelo email
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        # Pega o usuário encontrado (ou None)
        user = cursor.fetchone()
        conn.close()

        # Se o usuário existe, valida a senha
        if user:
            # user[2] é a senha salva no banco
            # agora é um hash (não é texto puro)
            senha_hash = user[2]

            # check_password_hash compara o hash do banco com a senha digitada
            if check_password_hash(senha_hash, senha):
                # Salva dados do usuário na sessão
                session['user_id'] = user[0]  # id do usuário
                session['nivel'] = user[3]    # 0 usuário | 1 atendente | 2 admin

                # Vai para o dashboard
                return redirect(url_for('dashboard'))

        # Se email não existir ou senha estiver errada
        return "Email ou senha inválidos!"

    # Se for GET, apenas exibe a página de login
    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    """
    Faz logout limpando a sessão e voltando para o login.
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
    - GET: mostra a página register.html
    - POST: cadastra usuário no banco com senha criptografada
    """

    if request.method == 'POST':
        # Captura email e senha digitados
        email = request.form['email']
        senha = request.form['senha']

        # Cria um hash seguro da senha
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insere o usuário como nível 0 (usuário comum)
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
    - Mostra lista de chamados conforme nível do usuário
    - Admin (nível 2) vê tudo (inclusive ocultos)
    - Usuário e atendente não veem ocultos
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ============================================================
    # ADMIN vê tudo (inclusive ocultos)
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
                attendant.email       -- ticket[9]
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        """)

    # ============================================================
    # Usuário e atendente só veem tickets visíveis (is_hidden = 0)
    # ============================================================
    else:
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
                attendant.email       -- ticket[9]
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            WHERE tickets.is_hidden = 0
            AND (tickets.user_id = ? OR ? IN (1))
        """, (session['user_id'], session.get('nivel')))

    # Retorna todos os tickets
    tickets = cursor.fetchall()
    conn.close()

    # Renderiza a página dashboard.html enviando a lista de tickets
    return render_template('dashboard.html', tickets=tickets)


# ============================================================
# CRIAR TICKET
# ============================================================

@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    """
    Criação de ticket:
    - GET: mostra create_ticket.html
    - POST: cria o ticket no banco com status "Aberto"
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Se o formulário foi enviado
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
            session['user_id'],  # usuário que criou
            datetime.now().strftime('%d/%m/%Y %H:%M'),  # data/hora atual
            0  # 0 = visível
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
    Inicia o atendimento:
    - Somente atendente (1) e admin (2)
    - Só inicia se o ticket estiver "Aberto"
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
        session['user_id'],  # atendente/admin que iniciou
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
    Fecha o chamado:
    - Somente atendente (1) e admin (2)
    - Só fecha se estiver "Em andamento"
    - Define closed_at
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
# OCULTAR CHAMADO (SOFT DELETE)
# ============================================================

@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
    """
    Oculta um chamado:
    - Não apaga do banco
    - Apenas marca is_hidden = 1
    - Somente atendente (1) e admin (2)
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
# DESOCULTAR CHAMADO (SOMENTE ADMIN)
# ============================================================

@app.route('/unhide-ticket/<int:ticket_id>')
def unhide_ticket(ticket_id):
    """
    Desoculta um chamado:
    - Somente admin (nível 2)
    - Marca is_hidden = 0 (volta a ficar visível)
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Se não for admin, não permite
    if session.get('nivel') != 2:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tickets SET is_hidden = 0 WHERE id = ?",
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
    # - reinicia automaticamente quando você salva o arquivo
    # - mostra erros detalhados no navegador
    app.run(debug=True)
