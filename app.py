from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave-secreta-simples'

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
            session['is_admin'] = user[3]
            return redirect(url_for('dashboard'))
        
        else:
            return "Email ou senha inválidos!"

    return render_template('login.html')

# ======================== LOGOUT ========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ======================== REGISTRO ========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, senha, is_admin) VALUES (?, ?, ?)",
            (email, senha, 0)
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

    if session.get('is_admin'):
        cursor.execute("""
            SELECT tickets.id,
                tickets.titulo,
                tickets.descricao,
                tickets.status,
                tickets.created_at,
                users.email
            FROM tickets
            JOIN users ON tickets.user_id = users.id
        """)
    else:
        cursor.execute("""
            SELECT tickets.id,
                tickets.titulo,
                tickets.descricao,
                tickets.status,
                tickets.created_at,
                users.email
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            WHERE tickets.user_id = ?
        """, (session['user_id'],))

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
        cursor.execute(
            "INSERT INTO tickets (titulo, descricao, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                titulo,
                descricao,
                'Aberto',
                session['user_id'],
                datetime.now().strftime('%d/%m/%Y %H:%M')
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    return render_template('create_ticket.html')

# ======================== STATUS TICKET ========================
@app.route('/update-status/<int:ticket_id>/<status>')
def update_status(ticket_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET status = ? WHERE id = ?",
        (status, ticket_id)
    )
        
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

# ======================== DELETE TICKET ========================
@app.route('/delete-ticket/<int:ticket_id>')
def delete_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tickets WHERE id = ?",
        (ticket_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# ======================== INICIAR API ========================
if __name__ == '__main__':
    app.run(debug=True)
