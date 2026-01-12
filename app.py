from flask import Flask, render_template, request
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
            return "Login realizado com sucesso!"
        
        else:
            return "Email ou senha inválidos!"

    return render_template('login.html')

# ======================== INICIAR API ========================
if __name__ == '__main__':
    app.run(debug=True)
