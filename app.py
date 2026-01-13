# Importa os módulos principais do Flask:
# - Flask: cria a aplicação
# - render_template: renderiza arquivos HTML dentro da pasta /templates
# - request: pega dados enviados por formulários (POST)
# - redirect: redireciona para outra rota
# - url_for: gera a URL de uma rota pelo nome da função
# - session: armazena dados do usuário logado (como user_id e nível)
from flask import Flask, render_template, request, redirect, url_for, session

# Importa o sqlite3 para conexão com banco SQLite
import sqlite3

# Importa datetime para salvar data/hora no chamado
from datetime import datetime


# Cria a aplicação Flask
app = Flask(__name__)

# Chave secreta para criptografar os dados da sessão
# (em produção isso deve ser algo mais forte e escondido)
app.secret_key = 'chave-secreta-simples'


# ======================== DB ========================
def get_db_connection():
    """
    Função responsável por abrir uma conexão com o banco SQLite.
    Sempre que precisar consultar/alterar o banco, você chama ela.
    """
    conn = sqlite3.connect('database.db')
    return conn


# ======================== LOGIN ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Tela de login:
    - GET: mostra a página login.html
    - POST: verifica se email e senha existem no banco
    """

    # Se o usuário enviou o formulário (POST)
    if request.method == 'POST':
        # Pega email e senha digitados no form
        email = request.form['email']
        senha = request.form['senha']

        # Conecta no banco
        conn = get_db_connection()
        cursor = conn.cursor()

        # Procura um usuário que tenha o email e senha informados
        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND senha = ?",
            (email, senha)
        )

        # Retorna o primeiro resultado encontrado (ou None)
        user = cursor.fetchone()

        # Fecha a conexão
        conn.close()

        # Se encontrou o usuário, faz login salvando dados na session
        if user:
            # user[0] normalmente é o ID do usuário (primeira coluna)
            session['user_id'] = user[0]

            # user[3] é o nível do usuário:
            # 0 usuário | 1 atendente | 2 admin
            session['nivel'] = user[3]

            # Redireciona para o dashboard
            return redirect(url_for('dashboard'))

        # Se não encontrou, retorna mensagem simples
        return "Email ou senha inválidos!"

    # Se for GET, apenas mostra a página de login
    return render_template('login.html')


# ======================== LOGOUT ========================
@app.route('/logout')
def logout():
    """
    Faz logout limpando a session.
    """
    session.clear()
    return redirect(url_for('login'))


# ======================== REGISTER ========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Cadastro de usuário:
    - GET: mostra o register.html
    - POST: cadastra no banco
    """

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Aqui você está inserindo um usuário como comum
        # OBS: Seu banco precisa ter a coluna correta.
        # Você colocou "is_admin", mas no resto do código você usa "nivel".
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
    """
    Dashboard:
    - Exibe os tickets (chamados)
    - Admin vê tudo (inclusive ocultos)
    - Usuário e atendente não veem ocultos
    """

    # Se não estiver logado, manda pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ADMIN (nível 2) vê todos os chamados, inclusive ocultos
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
        # Usuário e atendente não veem tickets ocultos
        # Também garante que:
        # - Usuário comum vê só os próprios tickets
        # - Atendente (nível 1) vê todos os tickets não ocultos
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

    # Pega todos os tickets retornados pela query
    tickets = cursor.fetchall()

    conn.close()

    # Renderiza a página dashboard.html enviando os tickets para o HTML
    return render_template('dashboard.html', tickets=tickets)


# ======================== CREATE TICKET ========================
@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    """
    Criação de ticket:
    - GET: mostra a tela create_ticket.html
    - POST: cria o ticket no banco
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

        # Cria o ticket como "Aberto"
        # Também salva o user_id do criador e a data/hora
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
            0  # 0 = visível, 1 = oculto
        ))

        conn.commit()
        conn.close()

        # Depois de criar, volta pro dashboard
        return redirect(url_for('dashboard'))

    # Se for GET, mostra a tela
    return render_template('create_ticket.html')


# ======================== START TICKET ========================
@app.route('/start-ticket/<int:ticket_id>')
def start_ticket(ticket_id):
    """
    Iniciar atendimento do ticket:
    - Somente atendente (1) ou admin (2)
    - Só inicia se o ticket estiver 'Aberto'
    - Salva quem iniciou (attendant_id) e o started_at
    """

    # Se não for atendente nem admin, não pode
    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Atualiza o ticket:
    # - muda status para "Em andamento"
    # - define o atendente como o usuário logado
    # - define started_at com data/hora atual
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
    """
    Fechar ticket:
    - Somente atendente (1) ou admin (2)
    - Só fecha se estiver 'Em andamento'
    - Define status como 'Fechado' e salva closed_at
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


# ======================== HIDE TICKET (SOFT DELETE) ========================
@app.route('/hide-ticket/<int:ticket_id>')
def hide_ticket(ticket_id):
    """
    Ocultar ticket (soft delete):
    - Não apaga do banco
    - Apenas marca is_hidden = 1
    - Somente atendente (1) ou admin (2)
    """

    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Marca o ticket como oculto
    cursor.execute(
        "UPDATE tickets SET is_hidden = 1 WHERE id = ?",
        (ticket_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ======================== START APP ========================
if __name__ == '__main__':
    # Inicia o servidor Flask em modo debug
    # Debug reinicia automaticamente ao salvar alterações
    app.run(debug=True)
