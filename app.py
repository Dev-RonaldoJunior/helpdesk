from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

PER_PAGE = 3

app = Flask(__name__)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# BANCO
# ============================================================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def now_str():
    return datetime.now().strftime('%d/%m/%Y %H:%M')


# ============================================================
# VALIDAR USERNAME
# ============================================================
def validar_username(username):
    if not username:
        return False

    username = username.strip().lower()
    padrao = r"^[a-z0-9]+\.[a-z0-9]+$"
    return re.match(padrao, username) is not None


# ============================================================
# FUNÇÃO: MARCAR COMO VISTO (SÓ PRA QUEM ABRIU)
# ============================================================
def marcar_ticket_como_visto(ticket_id):
    """
    Marca o ticket como visto dependendo do perfil logado:
    - user_seen_comment_id
    - attendant_seen_comment_id
    - admin_seen_comment_id

    Isso NÃO apaga notificação pros outros.
    """
    if "user_id" not in session:
        return

    nivel = session.get("nivel")
    user_id = session.get("user_id")

    if nivel not in [0, 1, 2]:
        return

    # Qual coluna vamos atualizar
    if nivel == 0:
        coluna = "user_seen_comment_id"
    elif nivel == 1:
        coluna = "attendant_seen_comment_id"
    else:
        coluna = "admin_seen_comment_id"

    conn = get_db_connection()
    cursor = conn.cursor()

    # pega o último comentário do ticket
    cursor.execute("""
        SELECT MAX(id) AS last_id
        FROM ticket_comments
        WHERE ticket_id = ?
    """, (ticket_id,))
    last_comment = cursor.fetchone()

    last_id = last_comment["last_id"] if last_comment and last_comment["last_id"] else None

    # Se não existe comentário, não precisa marcar nada
    if not last_id:
        conn.close()
        return

    # Atualiza o seen_comment_id do perfil atual
    cursor.execute(f"""
        UPDATE tickets
        SET {coluna} = ?
        WHERE id = ?
    """, (last_id, ticket_id))

    conn.commit()
    conn.close()


# ============================================================
# FUNÇÃO: CONTADOR DE NÃO LIDAS (SÓ DO OUTRO AUTOR)
# ============================================================
def get_unread_count(ticket_id):
    """
    Retorna quantas mensagens novas existem para o usuário logado
    considerando:
    - só conta mensagens feitas por OUTRA pessoa (user_id != logado)
    - usa seen_comment_id específico por perfil
    """
    if "user_id" not in session:
        return 0

    nivel = session.get("nivel")
    user_id = session.get("user_id")

    if nivel not in [0, 1, 2]:
        return 0

    if nivel == 0:
        coluna_seen = "user_seen_comment_id"
    elif nivel == 1:
        coluna_seen = "attendant_seen_comment_id"
    else:
        coluna_seen = "admin_seen_comment_id"

    conn = get_db_connection()
    cursor = conn.cursor()

    # pega o seen_comment_id atual
    cursor.execute(f"""
        SELECT {coluna_seen} AS seen_id
        FROM tickets
        WHERE id = ?
    """, (ticket_id,))
    row = cursor.fetchone()

    seen_id = row["seen_id"] if row and row["seen_id"] else 0

    # conta comentários novos (id > seen_id) feitos por OUTRO autor
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ticket_comments
        WHERE ticket_id = ?
          AND id > ?
          AND user_id != ?
    """, (ticket_id, seen_id, user_id))

    total = cursor.fetchone()["total"]
    conn.close()

    return total


def montar_unread_counts(tickets):
    """
    Recebe lista de tickets e devolve dict:
    { ticket_id: unread_count }
    """
    unread = {}
    for t in tickets:
        unread[t["id"]] = get_unread_count(t["id"])
    return unread


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
            senha_hash = user['senha']
            if check_password_hash(senha_hash, senha):
                session['user_id'] = user['id']
                session['nivel'] = user['is_admin']  # 0 user | 1 atendente | 2 admin
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('dashboard'))

        flash("Usuário ou senha inválidos!", "error")
        return redirect(url_for('login'))

    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
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
            flash("Username inválido! Use o formato nome.sobrenome (ex: joao.silva)", "error")
            return redirect(url_for('register'))

        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existe = cursor.fetchone()

        if existe:
            conn.close()
            flash("Esse username já existe! Escolha outro.", "warning")
            return redirect(url_for('register'))

        cursor.execute(
            "INSERT INTO users (username, email, senha, is_admin) VALUES (?, ?, ?, ?)",
            (username, None, senha_hash, 0)
        )

        conn.commit()
        conn.close()

        flash("Usuário cadastrado com sucesso! Agora faça login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ============================================================
# DASHBOARD (REDIRECIONA POR PERFIL)
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

        agora = now_str()

        cursor.execute("""
            INSERT INTO tickets
            (titulo, descricao, status, user_id, created_at, is_hidden)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            descricao,
            'Aberto',
            session['user_id'],
            agora,
            0
        ))

        conn.commit()
        conn.close()

        flash("Chamado criado com sucesso!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_ticket.html')


# ============================================================
# INICIAR ATENDIMENTO
# ============================================================
@app.route('/start-ticket/<int:ticket_id>')
def start_ticket(ticket_id):
    if session.get('nivel') not in [1, 2]:
        flash("Você não tem permissão para iniciar atendimento.", "error")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    agora = now_str()

    cursor.execute("""
        UPDATE tickets
        SET status = ?,
            attendant_id = ?,
            started_at = ?
        WHERE id = ?
          AND status = 'Aberto'
          AND is_hidden = 0
    """, (
        'Em andamento',
        session['user_id'],
        agora,
        ticket_id
    ))

    conn.commit()
    conn.close()

    flash(f"Chamado Nº: {ticket_id} iniciado com sucesso!", "success")
    return redirect(url_for('dashboard'))


# ============================================================
# FECHAR CHAMADO
# ============================================================
@app.route('/close-ticket/<int:ticket_id>')
def close_ticket(ticket_id):
    if session.get('nivel') not in [1, 2]:
        flash("Você não tem permissão para fechar chamado.", "error")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    agora = now_str()

    cursor.execute("""
        UPDATE tickets
        SET status = ?,
            closed_at = ?
        WHERE id = ?
          AND status = 'Em andamento'
          AND is_hidden = 0
    """, (
        'Fechado',
        agora,
        ticket_id
    ))

    conn.commit()
    conn.close()

    flash(f"Chamado Nº: {ticket_id} fechado com sucesso!", "success")
    return redirect(url_for('dashboard'))


# ============================================================
# OCULTAR CHAMADO (SOFT DELETE)
# ============================================================
@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
    if session.get('nivel') not in [1, 2]:
        flash("Você não tem permissão para ocultar chamados.", "error")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    agora = now_str()

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
        agora,
        ticket_id
    ))

    conn.commit()
    conn.close()

    flash(f"Chamado Nº: {ticket_id} foi ocultado.", "warning")
    return redirect(url_for('dashboard'))


# ============================================================
# DESOCULTAR (ADMIN)
# ============================================================
@app.route('/unhide-ticket/<int:ticket_id>')
def unhide_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 2:
        flash("Apenas administradores podem desocultar.", "error")
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

    flash(f"Chamado Nº: {ticket_id} foi desocultado.", "success")
    return redirect(url_for('dashboard'))


# ============================================================
# DETALHE DO CHAMADO + MARCAR COMO VISTO
# ============================================================
@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nivel = session.get('nivel')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Info do ticket (pra mensagem)
    cursor.execute("""
        SELECT
            tickets.id,
            tickets.status,
            tickets.is_hidden,
            tickets.user_id,
            tickets.attendant_id,
            attendant.username AS attendant_name
        FROM tickets
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.id = ?
    """, (ticket_id,))
    info = cursor.fetchone()

    if not info:
        conn.close()
        flash(f"Chamado Nº: {ticket_id} não encontrado.", "error")
        return redirect(url_for('dashboard'))

    status = info["status"]
    is_hidden = info["is_hidden"]
    atendente = info["attendant_name"] or "—"

    # Se ocultado:
    if is_hidden == 1 and nivel != 2:
        conn.close()
        flash(f"Chamado Nº: {ticket_id} não encontrado.", "error")
        return redirect(url_for('dashboard'))

    # Busca ticket completo com base no nível
    ticket = None

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
                creator.username AS creator_name,
                attendant.username AS attendant_name,
                hider.username AS hider_name,
                tickets.hidden_at
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
            WHERE tickets.id = ?
        """, (ticket_id,))
        ticket = cursor.fetchone()

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
                creator.username AS creator_name,
                attendant.username AS attendant_name,
                hider.username AS hider_name,
                tickets.hidden_at
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
            WHERE tickets.id = ?
              AND tickets.user_id = ?
              AND tickets.is_hidden = 0
        """, (ticket_id, session['user_id']))
        ticket = cursor.fetchone()

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
                creator.username AS creator_name,
                attendant.username AS attendant_name,
                hider.username AS hider_name,
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

    # Se não tem permissão
    if not ticket:
        conn.close()

        if status == "Em andamento":
            flash(f"Chamado Nº: {ticket_id} está sendo atendido por {atendente}.", "warning")
        elif status == "Fechado":
            flash(f"Chamado Nº: {ticket_id} foi encerrado por {atendente}.", "info")
        else:
            flash(f"Chamado Nº: {ticket_id} não encontrado.", "error")

        return redirect(url_for('dashboard'))

    # Comentários
    cursor.execute("""
        SELECT
            tc.id,
            tc.comment,
            tc.created_at,
            u.username AS author
        FROM ticket_comments tc
        JOIN users u ON tc.user_id = u.id
        WHERE tc.ticket_id = ?
        ORDER BY tc.id ASC
    """, (ticket_id,))
    comments = cursor.fetchall()

    conn.close()

    # Marca como visto só pra quem abriu
    marcar_ticket_como_visto(ticket_id)

    return render_template('ticket_detail.html', ticket=ticket, comments=comments)


# ============================================================
# PERMISSÃO DE COMENTAR
# ============================================================
def pode_comentar(ticket_id):
    nivel = session.get("nivel")
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            attendant_id,
            is_hidden
        FROM tickets
        WHERE id = ?
    """, (ticket_id,))
    t = cursor.fetchone()
    conn.close()

    if not t:
        return False

    # Admin pode comentar em qualquer
    if nivel == 2:
        return True

    # Ocultado: só admin
    if t["is_hidden"] == 1:
        return False

    # Usuário comenta no próprio ticket
    if nivel == 0:
        return t["user_id"] == user_id

    # Atendente comenta se for o responsável
    if nivel == 1:
        return t["attendant_id"] == user_id

    return False


# ============================================================
# ADICIONAR COMENTÁRIO
# ============================================================
@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
def add_comment(ticket_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    comment = request.form.get("comment", "").strip()

    if not comment:
        flash("Digite uma mensagem antes de enviar.", "warning")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    if not pode_comentar(ticket_id):
        flash(f"Chamado Nº: {ticket_id} não permite comentário.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor()

    agora = now_str()

    cursor.execute("""
        INSERT INTO ticket_comments (ticket_id, user_id, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        ticket_id,
        session["user_id"],
        comment,
        agora
    ))

    conn.commit()
    conn.close()

    flash(f"Comentário enviado no Chamado Nº: {ticket_id}.", "success")
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))


# ============================================================
# BUSCAR CHAMADO PELO NÚMERO
# ============================================================
@app.route('/buscar-ticket', methods=['GET'])
def buscar_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ticket_id = request.args.get('ticket_id', '').strip()

    if not ticket_id:
        flash("Digite o número do chamado.", "warning")
        return redirect(url_for('dashboard'))

    if not ticket_id.isdigit():
        flash("Digite apenas o número do chamado. Ex: 12", "error")
        return redirect(url_for('dashboard'))

    ticket_id = int(ticket_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, is_hidden
        FROM tickets
        WHERE id = ?
    """, (ticket_id,))
    ticket = cursor.fetchone()
    conn.close()

    if not ticket:
        flash(f"Chamado Nº: {ticket_id} não encontrado.", "error")
        return redirect(url_for('dashboard'))

    if ticket["is_hidden"] == 1 and session.get("nivel") != 2:
        flash(f"Chamado Nº: {ticket_id} não encontrado.", "error")
        return redirect(url_for('dashboard'))

    return redirect(url_for('ticket_detail', ticket_id=ticket_id))


# ============================================================
# PAGINAÇÃO POR STATUS
# ============================================================
def paginar_por_status(query_base, params_base, page):
    offset = (page - 1) * PER_PAGE

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) AS total FROM ({query_base})", params_base)
    total = cursor.fetchone()['total']

    cursor.execute(query_base + " ORDER BY tickets.id DESC LIMIT ? OFFSET ?",
                   params_base + (PER_PAGE, offset))
    itens = cursor.fetchall()

    conn.close()

    has_prev = page > 1
    has_next = (offset + PER_PAGE) < total

    return itens, has_prev, has_next


# ============================================================
# MEUS CHAMADOS (USUÁRIO)
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
            attendant.username AS attendant_name
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.is_hidden = 0
          AND tickets.user_id = ?
    """

    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Aberto'",
        (session['user_id'],),
        abertos_page
    )

    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Em andamento'",
        (session['user_id'],),
        andamento_page
    )

    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Fechado'",
        (session['user_id'],),
        fechados_page
    )

    # Monta unread_counts
    unread_counts = {}
    unread_counts.update(montar_unread_counts(abertos))
    unread_counts.update(montar_unread_counts(andamento))
    unread_counts.update(montar_unread_counts(fechados))

    return render_template(
        'meus_chamados_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,
        unread_counts=unread_counts,

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
# FILA (ATENDENTE)
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
            attendant.username AS attendant_name
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.is_hidden = 0
    """

    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Aberto'",
        (),
        abertos_page
    )

    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Em andamento' AND tickets.attendant_id = ?",
        (session['user_id'],),
        andamento_page
    )

    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_select + " AND tickets.status = 'Fechado' AND tickets.attendant_id = ?",
        (session['user_id'],),
        fechados_page
    )

    unread_counts = {}
    unread_counts.update(montar_unread_counts(abertos))
    unread_counts.update(montar_unread_counts(andamento))
    unread_counts.update(montar_unread_counts(fechados))

    return render_template(
        'fila_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,
        unread_counts=unread_counts,

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
# ADMIN
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
            attendant.username AS attendant_name,
            hider.username AS hider_name,
            tickets.hidden_at
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        WHERE 1 = 1
    """

    abertos, abertos_has_prev, abertos_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Aberto' AND tickets.is_hidden = 0",
        (),
        abertos_page
    )

    andamento, andamento_has_prev, andamento_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Em andamento' AND tickets.is_hidden = 0",
        (),
        andamento_page
    )

    fechados, fechados_has_prev, fechados_has_next = paginar_por_status(
        base_admin + " AND tickets.status = 'Fechado' AND tickets.is_hidden = 0",
        (),
        fechados_page
    )

    ocultados, ocultados_has_prev, ocultados_has_next = paginar_por_status(
        base_admin + " AND tickets.is_hidden = 1",
        (),
        ocultados_page
    )

    unread_counts = {}
    unread_counts.update(montar_unread_counts(abertos))
    unread_counts.update(montar_unread_counts(andamento))
    unread_counts.update(montar_unread_counts(fechados))
    unread_counts.update(montar_unread_counts(ocultados))

    return render_template(
        'admin_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,
        ocultados=ocultados,
        unread_counts=unread_counts,

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
# RUN
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)
