from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        return f"Email recebido: {email} e senha recebida: {senha}"
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)