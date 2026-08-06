import os
import socket
import psycopg2
from flask import Flask, jsonify, render_template_string, request, redirect, url_for

app = Flask(__name__)

# ── Configuração do banco ──────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "nordmart")
DB_USER = os.environ.get("DB_USER", "norddbadmin")
DB_PASS = os.environ.get("DB_PASS", "")

# ── Template HTML Completo (E-commerce + Admin + Busca) ────────
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NordMart - E-commerce Cloud Lab</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⬡</text></svg>">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Arial, sans-serif;
      background: #f4f6f9;
      color: #333;
    }
    header {
      background: #1a1a2e;
      color: white;
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 15px;
    }
    header h1 { font-size: 24px; letter-spacing: 2px; }
    .header-right {
      display: flex;
      align-items: center;
      gap: 15px;
    }
    header span {
      background: #e94560;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
    }
    .btn-toggle {
      background: #0f3460;
      color: white;
      border: 1px solid #e94560;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      cursor: pointer;
      text-decoration: none;
      font-weight: bold;
    }
    .btn-toggle:hover { background: #e94560; }

    .info-bar {
      background: #16213e;
      color: #aaa;
      text-align: center;
      padding: 8px;
      font-size: 12px;
    }
    .info-bar strong { color: #e94560; }
    .container { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
    h2 { margin-bottom: 15px; color: #1a1a2e; }

    /* Barra de Busca e Filtro */
    .search-bar {
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 25px;
      display: flex;
      gap: 10px;
    }
    .search-bar input {
      flex: 1;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    .search-bar button {
      background: #1a1a2e;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
    }

    /* Painel do Administrador */
    .admin-panel {
      background: #fff;
      border-left: 4px solid #e94560;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 30px;
    }
    .form-card {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 10px;
    }
    .form-card input {
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      flex: 1;
      min-width: 130px;
    }
    .form-card button {
      background: #e94560;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 20px;
    }
    .card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      text-align: center;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .card .emoji { font-size: 35px; margin-bottom: 8px; }
    .card h3 { font-size: 16px; margin-bottom: 6px; }
    .card .price {
      color: #e94560;
      font-weight: bold;
      font-size: 18px;
      margin-bottom: 6px;
    }
    .card .stock { color: #666; font-size: 13px; margin-bottom: 12px; }

    /* Ações de Compra (Cliente) */
    .buy-form {
      display: flex;
      gap: 5px;
      margin-top: 10px;
    }
    .buy-form input {
      width: 50px;
      padding: 6px;
      text-align: center;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    .btn-buy {
      flex: 1;
      background: #27ae60;
      color: white;
      border: none;
      padding: 6px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
      font-size: 12px;
    }
    .btn-buy:hover { background: #219653; }

    /* Ações de Admin nos Cards */
    .admin-actions {
      margin-top: 10px;
    }
    .btn-delete {
      width: 100%;
      background: #c0392b;
      color: white;
      border: none;
      padding: 6px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
      font-size: 12px;
      text-decoration: none;
      display: block;
      text-align: center;
    }
    .btn-delete:hover { background: #a93226; }

    .error {
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      color: #856404;
    }
    footer {
      text-align: center;
      padding: 30px;
      color: #888;
      font-size: 12px;
      margin-top: 40px;
    }
  </style>
</head>
<body>
  <header>
    <h1>⬡ NORDMART</h1>
    <div class="header-right">
      <span>Cloud Lab — Azure</span>
      {% if mode == 'admin' %}
        <a href="/?mode=client" class="btn-toggle">👤 Mudar para Visão Cliente</a>
      {% else %}
        <a href="/?mode=admin" class="btn-toggle">🛠️ Mudar para Visão Admin</a>
      {% endif %}
    </div>
  </header>

  <div class="info-bar">
    Servidor: <strong>{{ hostname }}</strong> &nbsp;|&nbsp;
    Zona: <strong>{{ zone }}</strong> &nbsp;|&nbsp;
    Banco: <strong>{{ db_status }}</strong> &nbsp;|&nbsp;
    Perfil: <strong>{{ 'Administrador' if mode == 'admin' else 'Cliente' }}</strong>
  </div>

  <div class="container">
    <!-- Barra de Busca -->
    <form class="search-bar" action="/" method="GET">
      <input type="hidden" name="mode" value="{{ mode }}">
      <input type="text" name="q" placeholder="Buscar produtos no catálogo..." value="{{ search_query }}">
      <button type="submit">Pesquisar</button>
    </form>

    <!-- Painel do Admin (Só aparece se o modo for admin) -->
    {% if mode == 'admin' %}
    <div class="admin-panel">
      <h2>🛠️ Painel Administrativo - Cadastrar Produto</h2>
      <form class="form-card" action="/add" method="POST">
        <input type="text" name="name" placeholder="Nome do Produto" required>
        <input type="number" step="0.01" name="price" placeholder="Preço (R$)" required>
        <input type="number" name="stock" placeholder="Estoque inicial" required>
        <input type="text" name="emoji" placeholder="Emoji (ex: 🚀)" value="📦" required>
        <button type="submit">Adicionar ao Banco</button>
      </form>
    </div>
    {% endif %}

    <h2>Catálogo de Produtos</h2>

    {% if error %}
    <div class="error">
      <strong>⚠ Banco de dados indisponível</strong><br>
      {{ error }}
    </div>
    {% elif not products %}
    <p style="text-align:center; color: #777; margin-top: 30px;">Nenhum produto encontrado.</p>
    {% else %}
    <div class="grid">
      {% for product in products %}
      <div class="card">
        <div>
          <div class="emoji">{{ product.emoji }}</div>
          <h3>{{ product.name }}</h3>
          <div class="price">R$ {{ "%.2f"|format(product.price) }}</div>
          <div class="stock">Estoque: <strong>{{ product.stock }}</strong> un</div>
        </div>

        <div>
          {% if mode == 'client' %}
            <!-- Formulário para comprar quantidade exata -->
            <form class="buy-form" action="/buy/{{ product.id }}" method="POST">
              <input type="number" name="quantity" value="1" min="1" max="{{ product.stock }}" required>
              <button type="submit" class="btn-buy">Comprar</button>
            </form>
          {% else %}
            <!-- Ações do Administrador -->
            <div class="admin-actions">
              <a href="/delete/{{ product.id }}" class="btn-delete" onclick="return confirm('Excluir este produto?')">Excluir Produto</a>
            </div>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <footer>
    NordMart &copy; 2026 — Infraestrutura Cloud Azure &nbsp;|&nbsp;
    Terraform + GitHub Actions
  </footer>
</body>
</html>
"""

# ── Funções auxiliares ─────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=5
    )

def setup_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INTEGER NOT NULL,
                emoji VARCHAR(10) DEFAULT '📦'
            )
        """)
        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]
        if count == 0:
            products = [
                ("Notebook Pro X", 4599.99, 15, "💻"),
                ("Smartphone NordX", 2199.99, 42, "📱"),
                ("Fone Bluetooth", 299.99, 80, "🎧"),
                ("Teclado Mecânico", 459.99, 30, "⌨️"),
                ("Monitor 27\"", 1899.99, 12, "🖥️"),
                ("Mouse Gamer", 189.99, 55, "🖱️"),
            ]
            cur.executemany(
                "INSERT INTO products (name, price, stock, emoji) VALUES (%s, %s, %s, %s)",
                products
            )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

def get_zone():
    hostname = socket.gethostname()
    if "vm-a" in hostname:
        return "Zone 1"
    elif "vm-b" in hostname:
        return "Zone 2"
    return "Unknown"

# ── Rotas ────────────────────────────────______________________
@app.route("/")
def index():
    hostname = socket.gethostname()
    zone = get_zone()
    mode = request.args.get("mode", "client")
    search_query = request.args.get("q", "").strip()
    products = []
    error = None
    db_status = "❌ Desconectado"

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if search_query:
            cur.execute(
                "SELECT id, name, price, stock, emoji FROM products WHERE name ILIKE %s ORDER BY id DESC",
                (f"%{search_query}%",)
            )
        else:
            cur.execute("SELECT id, name, price, stock, emoji FROM products ORDER BY id DESC")
            
        rows = cur.fetchall()
        products = [
            {"id": r[0], "name": r[1], "price": r[2], "stock": r[3], "emoji": r[4]}
            for r in rows
        ]
        cur.close()
        conn.close()
        db_status = "✅ Conectado"
    except Exception as e:
        error = str(e)

    return render_template_string(
        HTML,
        hostname=hostname,
        zone=zone,
        db_status=db_status,
        products=products,
        error=error,
        mode=mode,
        search_query=search_query
    )

@app.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    emoji = request.form.get("emoji", "📦")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, stock, emoji) VALUES (%s, %s, %s, %s)",
            (name, float(price), int(stock), emoji)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao inserir: {e}")

    return redirect(url_for("index", mode="admin"))

@app.route("/buy/<int:product_id>", methods=["POST"])
def buy_product(product_id):
    """Subtrai a quantidade exata digitada pelo cliente do estoque no banco."""
    quantity = int(request.form.get("quantity", 1))
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Subtrai garantindo que o estoque nunca fique abaixo de 0
        cur.execute(
            "UPDATE products SET stock = GREATEST(0, stock - %s) WHERE id = %s",
            (quantity, product_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar estoque: {e}")

    return redirect(url_for("index", mode="client"))

@app.route("/delete/<int:product_id>")
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao deletar: {e}")

    return redirect(url_for("index", mode="admin"))

@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "healthy",
            "hostname": socket.gethostname(),
            "database": "connected"
        }), 200
    except Exception:
        return jsonify({
            "status": "healthy",
            "hostname": socket.gethostname(),
            "database": "disconnected"
        }), 200


if __name__ == "__main__":
    setup_database()
    app.run(host="0.0.0.0", port=80, debug=False)
  