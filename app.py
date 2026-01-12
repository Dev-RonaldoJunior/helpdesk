from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave-secreta-simples'

# ======================== DB ========================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    return conn

# ======================== LOGIN ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND senha = ?",
            (email, senha)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['nivel'] = user[3]  # 0 usuário | 1 atendente | 2 admin
            return redirect(url_for('dashboard'))

        return "Email ou senha inválidos!"

    return render_template('login.html')

# ======================== LOGOUT ========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ======================== REGISTER ========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
            (email, senha, 0)  # usuário comum
        )
        conn.commit()
        conn.close()

        return "Usuário cadastrado com sucesso!"

    return render_template('register.html')

# ======================== DASHBOARD ========================
@app.route('/dashboard')
def dashboard():
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

    tickets = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', tickets=tickets)

# ======================== CREATE TICKET ========================
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

# ======================== START TICKET ========================
@app.route('/start-ticket/<int:ticket_id>')
def start_ticket(ticket_id):
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
        session['user_id'],
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        ticket_id
    ))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# ======================== CLOSE TICKET ========================
@app.route('/close-ticket/<int:ticket_id>')
def close_ticket(ticket_id):
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

# ======================== HIDE TICKET (SOFT DELETE) ========================
@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
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

# ======================== START APP ========================
if __name__ == '__main__':
    app.run(debug=True)
