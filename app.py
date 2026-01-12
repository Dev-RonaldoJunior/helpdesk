from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

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
            "INSERT INTO users (email, senha) VALUES (?, ?)",
            (email, senha)
        )
        conn.commit()
        conn.close()

        return "Usuário cadastrado com sucesso!"

    return render_template('register.html')

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
            return redirect(url_for('dashboard'))
        
        else:
            return "Email ou senha inválidos!"

    return render_template('login.html')

# ======================== DASHBOARD ========================
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets")
    tickets = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', tickets=tickets)

# ======================== CREATE TICKET ========================
@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tickets (titulo, descricao) VALUES (?, ?)",
            (titulo, descricao)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))
    
    return render_template('create_ticket.html')

# ======================== INICIAR API ========================
if __name__ == '__main__':
    app.run(debug=True)
