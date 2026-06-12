from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_da_loja' 

DB_PATH = "/home/chocoflow/chocolate.db"

def iniciar_banco():
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            imagem_url TEXT,
            ordem INTEGER DEFAULT 0,
            estoque INTEGER DEFAULT 10
        )
    ''')
    conexao.execute('''
        CREATE TABLE IF NOT EXISTS colecoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            imagem_url TEXT,
            ordem INTEGER DEFAULT 0,
            estoque INTEGER DEFAULT 10
        )
    ''')
    conexao.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    
    try:
        conexao.execute('ALTER TABLE produtos ADD COLUMN ordem INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
        
    try:
        conexao.execute('ALTER TABLE colecoes ADD COLUMN ordem INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass

    try:
        conexao.execute('ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 10')
    except sqlite3.OperationalError:
        pass
        
    try:
        conexao.execute('ALTER TABLE colecoes ADD COLUMN estoque INTEGER DEFAULT 10')
    except sqlite3.OperationalError:
        pass

    conexao.execute('UPDATE produtos SET ordem = id WHERE ordem = 0')
    conexao.execute('UPDATE colecoes SET ordem = id WHERE ordem = 0')
    
    conexao.commit()
    conexao.close()

iniciar_banco()

class ItemCarrinho:
    def __init__(self, id, nome, descricao, preco, tipo):
        self.id = id
        self.nome = nome
        self.descricao = descricao if descricao is not None else ""
        self.preco = preco
        self.tipo = tipo

@app.route('/')
def home():
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM produtos ORDER BY ordem ASC')
    linhas_prod = cursor.fetchall()
    todos_produtos = [{'id': l[0], 'nome': l[1], 'descricao': l[2], 'preco': l[3], 'imagem_url': l[4], 'estoque': l[5]} for l in linhas_prod]
        
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM colecoes ORDER BY ordem ASC')
    linhas_col = cursor.fetchall()
    lista_colecoes = [{'id': l[0], 'nome': l[1], 'descricao': l[2], 'preco': l[3], 'imagem_url': l[4], 'estoque': l[5]} for l in linhas_col]
        
    conexao.close()
    return render_template('produtos_lista.html', produtos=todos_produtos, colecoes=lista_colecoes)

@app.route('/buscar')
def buscar():
    termo = request.args.get('termo')
    pesquisa = f"%{termo}%"
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM produtos WHERE nome LIKE ? ORDER BY ordem ASC', (pesquisa,))
    linhas_prod = cursor.fetchall()
    produtos_encontrados = [{'id': l[0], 'nome': l[1], 'descricao': l[2], 'preco': l[3], 'imagem_url': l[4], 'estoque': l[5]} for l in linhas_prod]
    
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM colecoes WHERE nome LIKE ? ORDER BY ordem ASC', (pesquisa,))
    linhas_col = cursor.fetchall()
    colecoes_encontradas = [{'id': l[0], 'nome': l[1], 'descricao': l[2], 'preco': l[3], 'imagem_url': l[4], 'estoque': l[5]} for l in linhas_col]
    
    conexao.close()
    return render_template('produtos_lista.html', produtos=produtos_encontrados, colecoes=colecoes_encontradas)

@app.route('/produto/<int:id>')
def detalhes_produto(id):
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM produtos WHERE id = ?', (id,))
    linha = cursor.fetchone()
    conexao.close()
    
    if linha:
        produto = {
            'id': linha[0], 'nome': linha[1], 'descricao': linha[2], 'preco': linha[3],
            'imagem_url': linha[4] if linha[4] else "https://images.unsplash.com/photo-1548907040-4d42b52145ca?w=500",
            'estoque': linha[5],
            'tipo': 'produto'
        }
        return render_template('produto_detalhes.html', item=produto)
    flash('❌ Produto não encontrado!')
    return redirect(url_for('home'))

@app.route('/colecao/<int:id>')
def detalhes_colecao(id):
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM colecoes WHERE id = ?', (id,))
    linha = cursor.fetchone()
    conexao.close()
    
    if linha:
        colecao = {
            'id': linha[0], 'nome': linha[1], 'descricao': linha[2], 'preco': linha[3],
            'imagem_url': linha[4] if linha[4] else "https://images.unsplash.com/photo-1548907040-4d42b52145ca?w=500",
            'estoque': linha[5],
            'tipo': 'colecao'
        }
        return render_template('produto_detalhes.html', item=colecao)
    flash('❌ Coleção não encontrada!')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('senha') == 'mestre123':
            session['logado'] = True 
            flash('🔓 Bem-vindo ao painel admin!')
            return redirect(url_for('home'))
        else:
            flash('❌ Senha incorreta!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None) 
    return redirect(url_for('home'))

@app.route('/novo')
def novo():
    if not session.get('logado'): return redirect(url_for('login'))
    return render_template('novo.html')

@app.route('/salvar', methods=['POST'])
def salvar():
    if not session.get('logado'): return redirect(url_for('login'))
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    imagem_url = request.form.get('imagem_url', '')
    estoque = request.form.get('estoque', 10)
    
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('INSERT INTO produtos (nome, descricao, preco, imagem_url, estoque) VALUES (?, ?, ?, ?, ?)', 
                   (nome, descricao, preco, imagem_url, estoque))
    novo_id = cursor.lastrowid
    cursor.execute('UPDATE produtos SET ordem = ? WHERE id = ?', (novo_id, novo_id))
    conexao.commit()
    conexao.close()
    flash('🍫 Produto adicionado!')
    return redirect(url_for('home'))

@app.route('/editar/<int:id>')
def editar(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM produtos WHERE id = ?', (id,))
    linha = cursor.fetchone()
    conexao.close()
    if linha:
        produto = {'id': linha[0], 'nome': linha[1], 'descricao': linha[2], 'preco': linha[3], 'imagem_url': linha[4], 'estoque': linha[5]}
        return render_template('produtos_editar.html', produto=produto)
    return redirect(url_for('home'))

@app.route('/atualizar', methods=['POST'])
def atualizar():
    if not session.get('logado'): return redirect(url_for('login'))
    id = request.form['id']
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    imagem_url = request.form.get('imagem_url', '')
    estoque = request.form.get('estoque', 10)
    
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute('UPDATE produtos SET nome=?, descricao=?, preco=?, imagem_url=?, estoque=? WHERE id=?', 
                    (nome, descricao, preco, imagem_url, estoque, id))
    conexao.commit()
    conexao.close()
    return redirect(url_for('home'))

@app.route('/deletar/<int:id>')
def deletar(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('home'))

@app.route('/nova_colecao')
def nova_colecao():
    if not session.get('logado'): return redirect(url_for('login'))
    return render_template('nova_colecao.html')

@app.route('/salvar_colecao', methods=['POST'])
def salvar_colecao():
    if not session.get('logado'): return redirect(url_for('login'))
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    imagem_url = request.form.get('imagem_url', '')
    estoque = request.form.get('estoque', 10)
    
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('INSERT INTO colecoes (nome, descricao, preco, imagem_url, estoque) VALUES (?, ?, ?, ?, ?)', 
                   (nome, descricao, preco, imagem_url, estoque))
    novo_id = cursor.lastrowid
    cursor.execute('UPDATE colecoes SET ordem = ? WHERE id = ?', (novo_id, novo_id))
    conexao.commit()
    conexao.close()
    flash('🎁 Coleção adicionada!')
    return redirect(url_for('home'))

@app.route('/editar_colecao/<int:id>')
def editar_colecao(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome, descricao, preco, imagem_url, estoque FROM colecoes WHERE id = ?', (id,))
    linha = cursor.fetchone()
    conexao.close()
    if linha:
        colecao = {'id': linha[0], 'nome': linha[1], 'descricao': linha[2], 'preco': linha[3], 'imagem_url': linha[4], 'estoque': linha[5]}
        return render_template('editar_colecao.html', colecao=colecao)
    return redirect(url_for('home'))

@app.route('/atualizar_colecao', methods=['POST'])
def atualizar_colecao():
    if not session.get('logado'): return redirect(url_for('login'))
    id = request.form['id']
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    imagem_url = request.form.get('imagem_url', '')
    estoque = request.form.get('estoque', 10)
    
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute('UPDATE colecoes SET nome=?, descricao=?, preco=?, imagem_url=?, estoque=? WHERE id=?', 
                    (nome, descricao, preco, imagem_url, estoque, id))
    conexao.commit()
    conexao.close()
    return redirect(url_for('home'))

@app.route('/deletar_colecao/<int:id>')
def deletar_colecao(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute('DELETE FROM colecoes WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('home'))

@app.route('/mover_produto/<int:id>/<string:direcao>')
def mover_produto(id, direcao):
    if not session.get('logado'): return jsonify({'sucesso': False, 'erro': 'Não autorizado'}), 401
    
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    
    cursor.execute('SELECT ordem FROM produtos WHERE id = ?', (id,))
    linha = cursor.fetchone()
    if not linha:
        conexao.close()
        return jsonify({'sucesso': False, 'erro': 'Não encontrado'}), 404
    ordem_atual = linha[0]
    
    if direcao == 'esquerda':
        cursor.execute('SELECT id, ordem FROM produtos WHERE ordem < ? ORDER BY ordem DESC LIMIT 1', (ordem_atual,))
    else:
        cursor.execute('SELECT id, ordem FROM produtos WHERE ordem > ? ORDER BY ordem ASC LIMIT 1', (ordem_atual,))
        
    vizinho = cursor.fetchone()
    
    if vizinho:
        id_vizinho, ordem_vizinho = vizinho
        cursor.execute('UPDATE produtos SET ordem = ? WHERE id = ?', (ordem_vizinho, id))
        cursor.execute('UPDATE produtos SET ordem = ? WHERE id = ?', (ordem_atual, id_vizinho))
        conexao.commit()
        conexao.close()
        return jsonify({'sucesso': True, 'moveu': True})
        
    conexao.close()
    return jsonify({'sucesso': True, 'moveu': False})

@app.route('/mover_colecao/<int:id>/<string:direcao>')
def mover_colecao(id, direcao):
    if not session.get('logado'): return jsonify({'sucesso': False, 'erro': 'Não autorizado'}), 401
    
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    
    cursor.execute('SELECT ordem FROM colecoes WHERE id = ?', (id,))
    linha = cursor.fetchone()
    if not linha:
        conexao.close()
        return jsonify({'sucesso': False, 'erro': 'Não encontrado'}), 404
    ordem_atual = linha[0]
    
    if direcao == 'esquerda':
        cursor.execute('SELECT id, ordem FROM colecoes WHERE ordem < ? ORDER BY ordem DESC LIMIT 1', (ordem_atual,))
    else:
        cursor.execute('SELECT id, ordem FROM colecoes WHERE ordem > ? ORDER BY ordem ASC LIMIT 1', (ordem_atual,))
        
    vizinho = cursor.fetchone()
    
    if vizinho:
        id_vizinho, ordem_vizinho = vizinho
        cursor.execute('UPDATE colecoes SET ordem = ? WHERE id = ?', (ordem_vizinho, id))
        cursor.execute('UPDATE colecoes SET ordem = ? WHERE id = ?', (ordem_atual, id_vizinho))
        conexao.commit()
        conexao.close()
        return jsonify({'sucesso': True, 'moveu': True})
        
    conexao.close()
    return jsonify({'sucesso': True, 'moveu': False})

@app.route('/adicionar_carrinho/<string:tipo>/<int:id>')
def adicionar_carrinho(tipo, id):
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    tabela = 'produtos' if tipo == 'produto' else 'colecoes'
    cursor.execute(f'SELECT estoque FROM {tabela} WHERE id = ?', (id,))
    linha = cursor.fetchone()
    conexao.close()
    
    if linha and linha[0] <= 0:
        flash('❌ Desculpe, este item acabou de esgotar!')
        return redirect(request.referrer or url_for('home'))

    if 'carrinho' not in session: session['carrinho'] = []
    carrinho = session['carrinho']
    carrinho.append({'tipo': tipo, 'id': id})
    session['carrinho'] = carrinho
    flash('🛒 Item adicionado ao carrinho!')
    
    acao = request.args.get('acao')
    if acao == 'comprar':
        return redirect(url_for('ver_carrinho'))
    else:
        return redirect(request.referrer or url_for('home'))

@app.route('/carrinho')
def ver_carrinho():
    itens = session.get('carrinho', [])
    if not itens: return render_template('carrinho.html', produtos_carrinho=[], total=0)
    
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()
    produtos_carrinho = []
    total = 0
    for item in itens:
        if not isinstance(item, dict): continue
        tipo, id_item = item.get('tipo'), item.get('id')
        
        tabela = 'produtos' if tipo == 'produto' else 'colecoes'
        cursor.execute(f'SELECT id, nome, descricao, preco FROM {tabela} WHERE id = ?', (id_item,))
        linha = cursor.fetchone()
        
        if linha:
            produtos_carrinho.append(ItemCarrinho(linha[0], linha[1], linha[2], linha[3], tipo))
            total += linha[3]
            
    conexao.close()
    return render_template('carrinho.html', produtos_carrinho=produtos_carrinho, total=total)

@app.route('/remover_carrinho/<string:tipo>/<int:id>')
def remover_carrinho(tipo, id):
    if 'carrinho' in session:
        carrinho = session['carrinho']
        for item in carrinho:
            if item.get('tipo') == tipo and item.get('id') == id:
                carrinho.remove(item)
                break
        session['carrinho'] = carrinho
    return redirect(url_for('ver_carrinho'))

@app.route('/limpar_carrinho')
def limpar_carrinho():
    session.pop('carrinho', None)
    return redirect(url_for('ver_carrinho'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = generate_password_hash(request.form.get('senha'))
        try:
            conexao = sqlite3.connect(DB_PATH)
            conexao.execute('INSERT INTO clientes (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
            conexao.commit()
            conexao.close()
            flash('🎉 Conta criada com sucesso!')
            return redirect(url_for('login_cliente'))
        except sqlite3.IntegrityError:
            flash('❌ Este e-mail já está cadastrado!')
            return redirect(url_for('cadastro'))
    return render_template('cadastro.html')

@app.route('/login_cliente', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        conexao = sqlite3.connect(DB_PATH)
        cursor = conexao.cursor()
        cursor.execute('SELECT id, nome, senha FROM clientes WHERE email = ?', (email,))
        usuario = cursor.fetchone()
        conexao.close()
        if usuario and check_password_hash(usuario[2], senha):
            session['cliente_id'] = usuario[0]
            session['cliente_nome'] = usuario[1]
            return redirect(url_for('home'))
        else:
            flash('❌ E-mail ou senha incorretos.')
    return render_template('login_cliente.html')

@app.route('/logout_cliente')
def logout_cliente():
    session.pop('cliente_id', None)
    session.pop('cliente_nome', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)