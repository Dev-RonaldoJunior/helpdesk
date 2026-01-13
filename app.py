# ============================================================
# IMPORTAÇÕES
# ============================================================

# Flask:
# - Flask: cria o app
# - render_template: renderiza arquivos HTML dentro de /templates
# - request: pega dados enviados pelo formulário (POST)
# - redirect: redireciona para outra rota
# - url_for: gera URL de rotas pelo nome da função
# - session: guarda informações do usuário logado (id e nível)
from flask import Flask, render_template, request, redirect, url_for, session

# SQLite: banco de dados em arquivo (database.db)
import sqlite3

# datetime: para salvar datas (criação, início, fechamento, ocultação)
from datetime import datetime

# Segurança:
# - generate_password_hash: cria hash da senha no cadastro
# - check_password_hash: valida a senha digitada com o hash do banco
from werkzeug.security import generate_password_hash, check_password_hash

# re: expressões regulares para validar o formato do username
import re


# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

app = Flask(__name__)

# Chave secreta usada para criptografar/assinar dados da sessão
# Em produção: use uma chave forte e escondida (variável de ambiente)
app.secret_key = 'chave-secreta-simples'


# ============================================================
# FUNÇÃO PARA CONEXÃO COM O BANCO
# ============================================================

def get_db_connection():
    """
    Abre uma conexão com o banco SQLite.
    Sempre que precisar acessar o banco, use essa função.
    """
    conn = sqlite3.connect('database.db')
    return conn


# ============================================================
# VALIDAÇÃO DE USERNAME
# ============================================================

def validar_username(username):
    """
    Valida se o username está no formato:
    nome.sobrenome

    Regras:
    - só letras minúsculas (a-z)
    - números (0-9) são permitidos
    - precisa ter 1 ponto separando
    Exemplo válido: joao.silva
    Exemplo inválido: joao (sem ponto)
    Exemplo inválido: joao.silva.123 (2 pontos)
    """

    # Se não veio nada (vazio ou None), inválido
    if not username:
        return False

    # Remove espaços e força minúsculo
    username = username.strip().lower()

    # Regex:
    # ^ = início
    # [a-z0-9]+ = um ou mais letras/números
    # \. = ponto literal
    # [a-z0-9]+ = novamente um ou mais letras/números
    # $ = fim
    padrao = r"^[a-z0-9]+\.[a-z0-9]+$"

    # Retorna True se bater com o padrão, senão False
    return re.match(padrao, username) is not None


# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Tela de login:
    - GET: mostra login.html
    - POST: valida username + senha (hash)
    """

    # Se o formulário foi enviado
    if request.method == 'POST':
        # Pega o username digitado e padroniza
        username = request.form['username'].strip().lower()

        # Pega a senha digitada
        senha = request.form['senha']

        # Conecta ao banco
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca usuário pelo username
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        # Retorna o usuário encontrado (ou None)
        user = cursor.fetchone()
        conn.close()

        # Se encontrou usuário
        if user:
            # Estrutura da tabela users:
            # user[0] = id
            # user[1] = username
            # user[2] = email (pode ser NULL)
            # user[3] = senha (hash)
            # user[4] = is_admin (nível)
            senha_hash = user[3]

            # Confere se a senha digitada bate com o hash
            if check_password_hash(senha_hash, senha):
                # Salva dados do usuário na sessão
                session['user_id'] = user[0]
                session['nivel'] = user[4]  # 0 usuário | 1 atendente | 2 admin

                # Vai pro dashboard
                return redirect(url_for('dashboard'))

        # Se falhar, mostra mensagem
        return "Usuário ou senha inválidos!"

    # Se for GET, renderiza a página de login
    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    """
    Faz logout limpando a sessão.
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
    - POST: valida username, verifica duplicado e salva com hash
    """

    if request.method == 'POST':
        # Captura o username e padroniza
        username = request.form['username'].strip().lower()

        # Captura a senha
        senha = request.form['senha']

        # Valida se está no padrão nome.sobrenome
        if not validar_username(username):
            return "Username inválido! Use o formato nome.sobrenome (ex: fulano.detal)"

        # Gera o hash da senha
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica se username já existe
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existe = cursor.fetchone()

        # Se já existir, bloqueia cadastro
        if existe:
            conn.close()
            return "Esse username já existe! Escolha outro."

        # Insere o usuário no banco:
        # - email fica NULL (None)
        # - is_admin = 0 (usuário comum)
        cursor.execute(
            "INSERT INTO users (username, email, senha, is_admin) VALUES (?, ?, ?, ?)",
            (username, None, senha_hash, 0)
        )

        conn.commit()
        conn.close()

        return "Usuário cadastrado com sucesso! Agora faça login."

    # Se for GET, mostra a página de cadastro
    return render_template('register.html')


# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nivel = session.get('nivel')

    # 0 = usuário
    if nivel == 0:
        return redirect(url_for('meus_chamados'))

    # 1 = atendente
    if nivel == 1:
        return redirect(url_for('fila'))

    # 2 = admin
    if nivel == 2:
        return redirect(url_for('admin'))

    # caso algum usuário esteja com nível inválido
    return redirect(url_for('logout'))


    # ============================================================
    # ADMIN (nível 2) - vê tudo
    # ============================================================
    if session.get('nivel') == 2:
        cursor.execute("""
            SELECT
                tickets.id,           -- ticket[0]
                tickets.titulo,        -- ticket[1]
                tickets.descricao,     -- ticket[2]
                tickets.status,        -- ticket[3]
                tickets.created_at,    -- ticket[4]
                tickets.started_at,    -- ticket[5]
                tickets.closed_at,     -- ticket[6]
                tickets.is_hidden,     -- ticket[7]
                creator.username,      -- ticket[8]
                attendant.username,    -- ticket[9]
                hider.username,        -- ticket[10]
                tickets.hidden_at      -- ticket[11]
            FROM tickets
            JOIN users AS creator ON tickets.user_id = creator.id
            LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
            LEFT JOIN users AS hider ON tickets.hidden_by = hider.id
        """)

    else:
        # ============================================================
        # USUÁRIO COMUM (nível 0)
        # ============================================================
        if session.get('nivel') == 0:
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
                WHERE tickets.is_hidden = 0
                  AND tickets.user_id = ?
            """, (session['user_id'],))

        # ============================================================
        # ATENDENTE (nível 1)
        # ============================================================
        elif session.get('nivel') == 1:
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
                WHERE tickets.is_hidden = 0
                  AND (
                        tickets.status = 'Aberto'
                        OR tickets.attendant_id = ?
                      )
            """, (session['user_id'],))

    # Busca todos os tickets retornados
    tickets = cursor.fetchall()
    conn.close()

    # Envia os tickets para o HTML
    return render_template('dashboard.html', tickets=tickets)


# ============================================================
# CRIAR CHAMADO
# ============================================================

@app.route('/create-ticket', methods=['GET', 'POST'])
def create_ticket():
    """
    Cria um novo chamado:
    - GET: mostra o formulário
    - POST: salva no banco como "Aberto"
    """

    # Só logado pode criar chamado
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
    """
    Inicia atendimento do ticket:
    - Somente atendente (1) e admin (2)
    - Só inicia se status estiver "Aberto"
    """

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


# ============================================================
# FECHAR CHAMADO
# ============================================================

@app.route('/close-ticket/<int:ticket_id>')
def close_ticket(ticket_id):
    """
    Fecha o ticket:
    - Somente atendente (1) e admin (2)
    - Só fecha se status estiver "Em andamento"
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
    if session.get('nivel') not in [1, 2]:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Só pode ocultar se estiver fechado
    cursor.execute("""
        UPDATE tickets
        SET is_hidden = 1, hidden_by = ?, hidden_at = ?
        WHERE id = ?
          AND status = 'Fechado'
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
    """
    Desoculta o ticket:
    - Somente admin (2)
    - Marca is_hidden = 0
    - Limpa hidden_by e hidden_at
    """

    # Se não estiver logado, volta pro login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Só admin pode desocultar
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


@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Admin pode ver qualquer ticket (inclusive ocultado)
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

    # Usuário comum (nível 0) só pode ver o próprio ticket e não ocultado
    elif session.get('nivel') == 0:
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
        """, (ticket_id, session['user_id']))
        ticket = cursor.fetchone()

    # Atendente (nível 1) pode ver:
    # - tickets abertos (não ocultos)
    # - tickets que ele está atendendo (não ocultos)
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



@app.route('/meus-chamados')
def meus_chamados():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 0:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

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
            attendant.username
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.is_hidden = 0
          AND tickets.user_id = ?
        ORDER BY tickets.id DESC
    """, (session['user_id'],))

    tickets = cursor.fetchall()
    conn.close()

    abertos = [t for t in tickets if t[3] == 'Aberto']
    andamento = [t for t in tickets if t[3] == 'Em andamento']
    fechados = [t for t in tickets if t[3] == 'Fechado']

    return render_template(
        'meus_chamados_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados
    )




@app.route('/fila')
def fila():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 1:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Atendente vê:
    # - ABERTOS (para pegar)
    # - EM ANDAMENTO dele
    # - FECHADOS dele
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
            attendant.username
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        WHERE tickets.is_hidden = 0
          AND (
                tickets.status = 'Aberto'
                OR tickets.attendant_id = ?
              )
        ORDER BY tickets.id DESC
    """, (session['user_id'],))

    tickets = cursor.fetchall()
    conn.close()

    abertos = [t for t in tickets if t[3] == 'Aberto']
    andamento = [t for t in tickets if t[3] == 'Em andamento']
    fechados = [t for t in tickets if t[3] == 'Fechado']

    return render_template(
        'fila_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados
    )



@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('nivel') != 2:
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

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
            attendant.username
        FROM tickets
        JOIN users AS creator ON tickets.user_id = creator.id
        LEFT JOIN users AS attendant ON tickets.attendant_id = attendant.id
        ORDER BY tickets.id DESC
    """)

    tickets = cursor.fetchall()
    conn.close()

    abertos = [t for t in tickets if t[3] == 'Aberto' and t[7] == 0]
    andamento = [t for t in tickets if t[3] == 'Em andamento' and t[7] == 0]
    fechados = [t for t in tickets if t[3] == 'Fechado' and t[7] == 0]
    ocultados = [t for t in tickets if t[7] == 1]

    return render_template(
        'admin_kanban.html',
        abertos=abertos,
        andamento=andamento,
        fechados=fechados,
        ocultados=ocultados
    )


# ============================================================
# INICIAR A APLICAÇÃO
# ============================================================

if __name__ == '__main__':
    # debug=True:
    # - reinicia o servidor automaticamente ao salvar
    # - mostra erros detalhados no navegador
    app.run(debug=True)
