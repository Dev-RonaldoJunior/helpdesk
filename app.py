# ============================================================
# IMPORTAÇÕES
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

PER_PAGE = 3

# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

app = Flask(__name__)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# FUNÇÃO PARA CONEXÃO COM O BANCO
# ============================================================

def get_db_connection():
    conn = sqlite3.connect('database.db')
    return conn


# ============================================================
# VALIDAÇÃO DE USERNAME
# ============================================================

def validar_username(username):
    if not username:
        return False

    username = username.strip().lower()
    padrao = r"^[a-z0-9]+\.[a-z0-9]+$"
    return re.match(padrao, username) is not None


# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # users:
            # user[0] = id
            # user[1] = username
            # user[2] = email
            # user[3] = senha_hash
            # user[4] = is_admin (nível)
            senha_hash = user[3]

            if check_password_hash(senha_hash, senha):
                session['user_id'] = user[0]
                session['nivel'] = user[4]
                return redirect(url_for('dashboard'))

        return "Usuário ou senha inválidos!"

    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# REGISTER
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        senha = request.form['senha']

        if not validar_username(username):
            return "Username inválido! Use o formato nome.sobrenome (ex: fulano.detal)"

        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existe = cursor.fetchone()

        if existe:
            conn.close()
            return "Esse username já existe! Escolha outro."

        cursor.execute(
            "INSERT INTO users (username, email, senha, is_admin) VALUES (?, ?, ?, ?)",
            (username, None, senha_hash, 0)
        )

        conn.commit()
        conn.close()

        return "Usuário cadastrado com sucesso! Agora faça login."

    return render_template('register.html')


# ============================================================
# DASHBOARD REDIRECT
# ============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nivel = session.get('nivel')

    if nivel == 0:
        return redirect(url_for('meus_chamados'))

    if nivel == 1:
        return redirect(url_for('fila'))

    if nivel == 2:
        return redirect(url_for('admin'))

    return redirect(url_for('logout'))


# ============================================================
# CRIAR CHAMADO
# ============================================================

@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
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
            'Aberto',
            session['user_id'],
            datetime.now().strftime('%d/%m/%Y %H:%M'),
            0
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
    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?, attendant_id = ?, started_at = ?
        WHERE id = ? AND status = 'Aberto' AND is_hidden = 0
    """, (
        'Em andamento',
        session['user_id'],
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
    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?, closed_at = ?
        WHERE id = ? AND status = 'Em andamento' AND is_hidden = 0
    """, (
        'Fechado',
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        ticket_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ============================================================
# OCULTAR CHAMADO (SÓ SE ESTIVER FECHADO)
# ============================================================

@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
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
          AND status = 'Fechado'
          AND is_hidden = 0
    """, (
        session['user_id'],
        datetime.now().strftime('%d/%m/%Y %H:%M'),
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
# DETALHES DO CHAMADO
# ============================================================

@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nivel = session.get('nivel')

    conn = get_db_connection()
    cursor = conn.cursor()

    # ADMIN vê tudo
    if nivel == 2:
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
                creator.username,
                attendant.username,
                hider.username,
                tickets.hidden_at
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
            WHERE tickets.id = ?
        """, (ticket_id,))
        ticket = cursor.fetchone()

    # USUÁRIO vê só o dele e não oculto
    elif nivel == 0:
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
                creator.username,
                attendant.username,
                hider.username,
                tickets.hidden_at
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
            WHERE tickets.id = ?
              AND tickets.user_id = ?
              AND tickets.is_hidden = 0
              AND (
                    tickets.status = 'Aberto'
                    OR tickets.attendant_id IS NULL
                    OR tickets.attendant_id = ?
                  )
        """, (ticket_id, session['user_id'], session['user_id']))
        ticket = cursor.fetchone()

    # ATENDENTE vê:
    # - abertos (não ocultos)
    # - em andamento/fechado apenas se ele for o attendant_id
    else:
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
                creator.username,
                attendant.username,
                hider.username,
                tickets.hidden_at
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
            WHERE tickets.id = ?
              AND tickets.is_hidden = 0
              AND (
                    tickets.status = 'Aberto'
                    OR tickets.attendant_id = ?
                  )
        """, (ticket_id, session['user_id']))
        ticket = cursor.fetchone()

    conn.close()

    if not ticket:
        return "Chamado não encontrado ou você não tem permissão para ver."

    return render_template('ticket_detail.html', ticket=ticket)


# ============================================================
# FUNÇÃO AUXILIAR: PAGINAÇÃO POR STATUS
# ============================================================

def paginar_por_status(query_base, params_base, page):
    offset = (page - 1) * PER_PAGE

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total
    cursor.execute(f"SELECT COUNT(*) FROM ({query_base})", params_base)
    total = cursor.fetchone()[0]

    # Página
    cursor.execute(query_base + " ORDER BY tickets.id DESC LIMIT ? OFFSET ?",
                   params_base + (PER_PAGE, offset))
    itens = cursor.fetchall()

    conn.close()

    has_prev = page > 1
    has_next = (offset + PER_PAGE) < total

    return itens, has_prev, has_next


# ============================================================
# MEUS CHAMADOS (USUÁRIO) - PAGINAÇÃO POR COLUNA
# ============================================================

@app.route('/meus-chamados')
def meus_chamados():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 0:
        return redirect(url_for('dashboard'))

    abertos_page = int(request.args.get('abertos_page', 1))
    andamento_page = int(request.args.get('andamento_page', 1))
    fechados_page = int(request.args.get('fechados_page', 1))

    base_select = """
        SELECT
            tickets.id,
            tickets.titulo,
            tickets.descricao,
            tickets.status,
            tickets.created_at,
            tickets.started_at,
            tickets.closed_at,
            tickets.is_hidden,
            creator.username,
            attendant.username
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.is_hidden = 0
          AND tickets.user_id = ?
    """

    # ABERTOS
    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Aberto'",
        (session['user_id'],),
        abertos_page
    )

    # ANDAMENTO (só aparece se for dele ou se o atendente for ele)
    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Em andamento'",
        (session['user_id'],),
        andamento_page
    )

    # FECHADOS
    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Fechado'",
        (session['user_id'],),
        fechados_page
    )

    return render_template(
        'meus_chamados_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,

        abertos_page=abertos_page,
        abertos_has_prev=abertos_has_prev,
        abertos_has_next=abertos_has_next,

        andamento_page=andamento_page,
        andamento_has_prev=andamento_has_prev,
        andamento_has_next=andamento_has_next,

        fechados_page=fechados_page,
        fechados_has_prev=fechados_has_prev,
        fechados_has_next=fechados_has_next
    )


# ============================================================
# FILA (ATENDENTE) - PAGINAÇÃO POR COLUNA
# ============================================================

@app.route('/fila')
def fila():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 1:
        return redirect(url_for('dashboard'))

    abertos_page = int(request.args.get('abertos_page', 1))
    andamento_page = int(request.args.get('andamento_page', 1))
    fechados_page = int(request.args.get('fechados_page', 1))

    # ABERTOS: todo mundo atendente vê
    base_abertos = """
        SELECT
            tickets.id,
            tickets.titulo,
            tickets.descricao,
            tickets.status,
            tickets.created_at,
            tickets.started_at,
            tickets.closed_at,
            tickets.is_hidden,
            creator.username,
            attendant.username,
            hider.username,
            tickets.hidden_at
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        WHERE tickets.is_hidden = 0
          AND tickets.status = 'Aberto'
    """

    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_abertos,
        (),
        abertos_page
    )

    # EM ANDAMENTO: atendente vê só os dele
    base_andamento = """
        SELECT
            tickets.id,
            tickets.titulo,
            tickets.descricao,
            tickets.status,
            tickets.created_at,
            tickets.started_at,
            tickets.closed_at,
            tickets.is_hidden,
            creator.username,
            attendant.username,
            hider.username,
            tickets.hidden_at
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        WHERE tickets.is_hidden = 0
          AND tickets.status = 'Em andamento'
          AND tickets.attendant_id = ?
    """

    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_andamento,
        (session['user_id'],),
        andamento_page
    )

    # FECHADOS: atendente vê só os dele
    base_fechados = """
        SELECT
            tickets.id,
            tickets.titulo,
            tickets.descricao,
            tickets.status,
            tickets.created_at,
            tickets.started_at,
            tickets.closed_at,
            tickets.is_hidden,
            creator.username,
            attendant.username,
            hider.username,
            tickets.hidden_at
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        WHERE tickets.is_hidden = 0
          AND tickets.status = 'Fechado'
          AND tickets.attendant_id = ?
    """

    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_fechados,
        (session['user_id'],),
        fechados_page
    )

    return render_template(
        'fila_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,

        abertos_page=abertos_page,
        abertos_has_prev=abertos_has_prev,
        abertos_has_next=abertos_has_next,

        andamento_page=andamento_page,
        andamento_has_prev=andamento_has_prev,
        andamento_has_next=andamento_has_next,

        fechados_page=fechados_page,
        fechados_has_prev=fechados_has_prev,
        fechados_has_next=fechados_has_next
    )


# ============================================================
# ADMIN - PAGINAÇÃO POR COLUNA + OCULTADOS
# ============================================================

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 2:
        return redirect(url_for('dashboard'))

    abertos_page = int(request.args.get('abertos_page', 1))
    andamento_page = int(request.args.get('andamento_page', 1))
    fechados_page = int(request.args.get('fechados_page', 1))
    ocultados_page = int(request.args.get('ocultados_page', 1))

    base_admin = """
        SELECT
            tickets.id,
            tickets.titulo,
            tickets.descricao,
            tickets.status,
            tickets.created_at,
            tickets.started_at,
            tickets.closed_at,
            tickets.is_hidden,
            creator.username,
            attendant.username,
            hider.username,
            tickets.hidden_at
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        WHERE 1 = 1
    """

    # ABERTOS
    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Aberto' AND tickets.is_hidden = 0",
        (),
        abertos_page
    )

    # ANDAMENTO
    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Em andamento' AND tickets.is_hidden = 0",
        (),
        andamento_page
    )

    # FECHADOS
    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Fechado' AND tickets.is_hidden = 0",
        (),
        fechados_page
    )

    # OCULTADOS
    ocultados, ocultados_has_prev, ocultados_has_next = paginar_por_status(
        base_admin + " AND tickets.is_hidden = 1",
        (),
        ocultados_page
    )

    return render_template(
        'admin_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,
        ocultados=ocultados,

        abertos_page=abertos_page,
        abertos_has_prev=abertos_has_prev,
        abertos_has_next=abertos_has_next,

        andamento_page=andamento_page,
        andamento_has_prev=andamento_has_prev,
        andamento_has_next=andamento_has_next,

        fechados_page=fechados_page,
        fechados_has_prev=fechados_has_prev,
        fechados_has_next=fechados_has_next,

        ocultados_page=ocultados_page,
        ocultados_has_prev=ocultados_has_prev,
        ocultados_has_next=ocultados_has_next
    )


# ============================================================
# START APP
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)
