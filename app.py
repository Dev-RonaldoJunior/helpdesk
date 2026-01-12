from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'chave-secreta-simples'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    return conn

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

# ======================== LOGIN/LOGOUT ========================
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ======================== DASHBOARD ========================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    if session.get('is_admin'):
        cursor.execute("SELECT * FROM tickets")
    else:
        cursor.execute(
            "SELECT * FROM tickets WHERE user_id = ?",
            (session['user_id'],)
        )

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
            "INSERT INTO tickets (titulo, descricao, status, user_id) VALUES (?, ?, ?, ?)",
            (titulo, descricao, 'Aberto', session['user_id'])
        )
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))
    
    return render_template('create_ticket.html')

@app.route('/update-status/<int:ticket_id>/<status>')
def update_status(ticket_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if session.get('is_admin'):
        cursor.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (status, ticket_id)
        )
    else:
        cursor.execute(
        "UPDATE tickets SET status = ? WHERE id = ? AND user_id = ?",
        (status, ticket_id, session['user_id'])
    )
        
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# ======================== INICIAR API ========================
if __name__ == '__main__':
    app.run(debug=True)
