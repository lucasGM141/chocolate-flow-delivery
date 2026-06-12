import sqlite3
from produto import Produto

class ProdutoDAO:
    def __init__(self):
        # Caminho absoluto fixo para não haver desalinhamento de pastas
        self.db_path = "/home/chocoflow/chocolate.db"
        self._criar_tabela()

    def _criar_tabela(self):
        conexao = sqlite3.connect(self.db_path)
        conexao.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco REAL NOT NULL,
                imagem_url TEXT
            )
        ''')
        conexao.commit()
        conexao.close()

    def listar_todos(self):
        self._criar_tabela()
        conexao = sqlite3.connect(self.db_path)
        cursor = conexao.cursor()
        cursor.execute('SELECT id, nome, descricao, preco FROM produtos')
        linhas = cursor.fetchall()
        conexao.close()
        
        produtos = []
        for linha in linhas:
            p = Produto(nome=linha[1], descricao=linha[2], preco=linha[3])
            p.id = linha[0]
            produtos.append(p)
        return produtos