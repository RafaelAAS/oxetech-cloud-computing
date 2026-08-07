import os
import socket
import psycopg2
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nordmart-lab-secret-key-2026")

# ── Configuração do banco ──────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "nordmart")
DB_USER = os.environ.get("DB_USER", "norddbadmin")
DB_PASS = os.environ.get("DB_PASS", "")

CATEGORIES = ["Todos", "Informática", "Acessórios", "Áudio", "Periféricos"]

# ── Template HTML Completo (E-commerce + Admin + Carrinho) ─────
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
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f4f6f9;
      color: #333;
    }
    header {
      background: #1a1a2e;
      color: white;
      padding: 18px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 15px;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    header h1 { font-size: 24px; letter-spacing: 2px; }
    .header-right {
      display: flex;
      align-items: center;
      gap: 15px;
    }
    header span.badge {
      background: #e94560;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
    }
    .btn-toggle, .btn-cart {
      background: #0f3460;
      color: white;
      border: 1px solid #e94560;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 13px;
      cursor: pointer;
      text-decoration: none;
      font-weight: bold;
      position: relative;
    }
    .btn-toggle:hover, .btn-cart:hover { background: #e94560; }
    .cart-count {
      background: #e94560;
      color: white;
      border-radius: 50%;
      padding: 2px 7px;
      font-size: 11px;
      margin-left: 6px;
    }

    .info-bar {
      background: #16213e;
      color: #aaa;
      text-align: center;
      padding: 8px;
      font-size: 12px;
    }
    .info-bar strong { color: #e94560; }
    .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
    h2 { margin-bottom: 15px; color: #1a1a2e; }

    /* Barra de Busca e Filtro */
    .toolbar {
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 25px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .toolbar input[type=text] {
      flex: 2;
      min-width: 200px;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    .toolbar select {
      flex: 1;
      min-width: 150px;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
    }
    .toolbar button {
      background: #1a1a2e;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
    }

    /* Banner promocional */
    .banner {
      background: linear-gradient(135deg, #e94560, #0f3460);
      color: white;
      padding: 25px 30px;
      border-radius: 8px;
      margin-bottom: 25px;
      text-align: center;
    }
    .banner h2 { color: white; margin-bottom: 5px; }
    .banner p { font-size: 14px; opacity: 0.9; }

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
    .form-card input, .form-card select {
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

    .orders-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    .orders-table th, .orders-table td {
      padding: 10px;
      border-bottom: 1px solid #eee;
      text-align: left;
    }
    .orders-table th { color: #666; text-transform: uppercase; font-size: 11px; }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
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
      position: relative;
      transition: transform 0.15s ease;
    }
    .card:hover { transform: translateY(-3px); }
    .category-tag {
      position: absolute;
      top: 10px;
      left: 10px;
      background: #f0f0f5;
      color: #555;
      font-size: 10px;
      padding: 3px 8px;
      border-radius: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .stock-badge {
      position: absolute;
      top: 10px;
      right: 10px;
      font-size: 10px;
      padding: 3px 8px;
      border-radius: 10px;
      font-weight: bold;
    }
    .stock-ok { background: #eafaf1; color: #27ae60; }
    .stock-low { background: #fef5e7; color: #e67e22; }
    .stock-out { background: #fdecea; color: #c0392b; }

    .card .emoji { font-size: 40px; margin: 20px 0 8px; }
    .card h3 { font-size: 16px; margin-bottom: 6px; }
    .card .price {
      color: #e94560;
      font-weight: bold;
      font-size: 19px;
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
      width: 55px;
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
      padding: 8px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
      font-size: 12px;
    }
    .btn-buy:hover { background: #219653; }
    .btn-buy:disabled { background: #ccc; cursor: not-allowed; }

    /* Ações de Admin nos Cards */
    .admin-actions { margin-top: 10px; }
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
    .success-box {
      background: #eafaf1;
      border: 1px solid #27ae60;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      color: #1e8449;
      margin-bottom: 25px;
    }

    /* Carrinho */
    .cart-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: white;
      border-radius: 6px;
      margin-bottom: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .cart-total {
      text-align: right;
      font-size: 20px;
      font-weight: bold;
      color: #1a1a2e;
      margin: 20px 0;
    }
    .btn-checkout {
      background: #27ae60;
      color: white;
      border: none;
      padding: 14px 28px;
      border-radius: 6px;
      font-size: 15px;
      font-weight: bold;
      cursor: pointer;
      float: right;
    }
    .empty-cart { text-align: center; color: #888; padding: 40px 0; }

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
      <span class="badge">Cloud Lab — Azure</span>
      <a href="/cart" class="btn-cart">🛒 Carrinho <span class="cart-count">{{ cart_count }}</span></a>
      {% if mode == 'admin' %}
        <a href="/?mode=client" class="btn-toggle">👤 Visão Cliente</a>
      {% else %}
        <a href="/?mode=admin" class="btn-toggle">🛠️ Visão Admin</a>
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
    {% if flash_message %}
    <div class="success-box">{{ flash_message }}</div>
    {% endif %}

    {% if mode == 'client' %}
    <div class="banner">
      <h2>🎉 Semana NordMart de Ofertas</h2>
      <p>Frete grátis para compras acima de R$ 300 — Estoque atualizado em tempo real</p>
    </div>
    {% endif %}

    <!-- Barra de Busca e Filtro -->
    <form class="toolbar" action="/" method="GET">
      <input type="hidden" name="mode" value="{{ mode }}">
      <input type="text" name="q" placeholder="Buscar produtos no catálogo..." value="{{ search_query }}">
      <select name="category" onchange="this.form.submit()">
        {% for cat in categories %}
        <option value="{{ cat }}" {% if cat == selected_category %}selected{% endif %}>{{ cat }}</option>
        {% endfor %}
      </select>
      <select name="sort" onchange="this.form.submit()">
        <option value="" {% if sort_by == '' %}selected{% endif %}>Mais recentes</option>
        <option value="price_asc" {% if sort_by == 'price_asc' %}selected{% endif %}>Menor preço</option>
        <option value="price_desc" {% if sort_by == 'price_desc' %}selected{% endif %}>Maior preço</option>
      </select>
      <button type="submit">Filtrar</button>
    </form>

    <!-- Painel do Admin -->
    {% if mode == 'admin' %}
    <div class="admin-panel">
      <h2>🛠️ Painel Administrativo - Cadastrar Produto</h2>
      <form class="form-card" action="/add" method="POST">
        <input type="text" name="name" placeholder="Nome do Produto" required>
        <select name="category" required>
          {% for cat in categories[1:] %}
          <option value="{{ cat }}">{{ cat }}</option>
          {% endfor %}
        </select>
        <input type="number" step="0.01" name="price" placeholder="Preço (R$)" required>
        <input type="number" name="stock" placeholder="Estoque inicial" required>
        <input type="text" name="emoji" placeholder="Emoji (ex: 🚀)" value="📦" required>
        <button type="submit">Adicionar ao Banco</button>
      </form>
    </div>

    <div class="admin-panel">
      <h2>📋 Últimos Pedidos</h2>
      {% if orders %}
      <table class="orders-table">
        <tr><th>#</th><th>Produto</th><th>Qtd</th><th>Total</th><th>Data</th></tr>
        {% for o in orders %}
        <tr>
          <td>{{ o.id }}</td>
          <td>{{ o.product_name }}</td>
          <td>{{ o.quantity }}</td>
          <td>R$ {{ "%.2f"|format(o.total) }}</td>
          <td>{{ o.created_at }}</td>
        </tr>
        {% endfor %}
      </table>
      {% else %}
      <p style="color:#888; padding: 10px 0;">Nenhum pedido registrado ainda.</p>
      {% endif %}
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
        <span class="category-tag">{{ product.category }}</span>
        {% if product.stock == 0 %}
          <span class="stock-badge stock-out">Esgotado</span>
        {% elif product.stock <= 10 %}
          <span class="stock-badge stock-low">Últimas unidades</span>
        {% else %}
          <span class="stock-badge stock-ok">Disponível</span>
        {% endif %}

        <div>
          <div class="emoji">{{ product.emoji }}</div>
          <h3>{{ product.name }}</h3>
          <div class="price">R$ {{ "%.2f"|format(product.price) }}</div>
          <div class="stock">Estoque: <strong>{{ product.stock }}</strong> un</div>
        </div>

        <div>
          {% if mode == 'client' %}
            <form class="buy-form" action="/cart/add/{{ product.id }}" method="POST">
              <input type="number" name="quantity" value="1" min="1" max="{{ product.stock }}" {% if product.stock == 0 %}disabled{% endif %} required>
              <button type="submit" class="btn-buy" {% if product.stock == 0 %}disabled{% endif %}>
                {{ 'Esgotado' if product.stock == 0 else '+ Carrinho' }}
              </button>
            </form>
          {% else %}
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

CART_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Carrinho - NordMart</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #333; }
    header {
      background: #1a1a2e; color: white; padding: 18px 40px;
      display: flex; justify-content: space-between; align-items: center;
    }
    header h1 { font-size: 22px; letter-spacing: 2px; }
    header a { color: white; text-decoration: none; font-size: 13px; background: #0f3460; padding: 8px 16px; border-radius: 20px; }
    .container { max-width: 700px; margin: 40px auto; padding: 0 20px; }
    h2 { margin-bottom: 20px; color: #1a1a2e; }
    .cart-item {
      display: flex; justify-content: space-between; align-items: center;
      padding: 15px; background: white; border-radius: 6px; margin-bottom: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .cart-item .info { display: flex; align-items: center; gap: 15px; }
    .cart-item .emoji { font-size: 28px; }
    .cart-item .qty { color: #666; font-size: 13px; }
    .remove-btn { background: #c0392b; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .cart-total { text-align: right; font-size: 20px; font-weight: bold; color: #1a1a2e; margin: 25px 0; }
    .btn-checkout {
      background: #27ae60; color: white; border: none; padding: 14px 28px;
      border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer; float: right;
    }
    .empty-cart { text-align: center; color: #888; padding: 60px 0; }
    .empty-cart a { color: #e94560; font-weight: bold; }
  </style>
</head>
<body>
  <header>
    <h1>⬡ NORDMART</h1>
    <a href="/">← Continuar comprando</a>
  </header>
  <div class="container">
    <h2>🛒 Seu Carrinho</h2>
    {% if items %}
      {% for item in items %}
      <div class="cart-item">
        <div class="info">
          <span class="emoji">{{ item.emoji }}</span>
          <div>
            <div><strong>{{ item.name }}</strong></div>
            <div class="qty">{{ item.quantity }} un × R$ {{ "%.2f"|format(item.price) }}</div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:15px;">
          <strong>R$ {{ "%.2f"|format(item.quantity * item.price) }}</strong>
          <form action="/cart/remove/{{ item.id }}" method="POST">
            <button type="submit" class="remove-btn">Remover</button>
          </form>
        </div>
      </div>
      {% endfor %}
      <div class="cart-total">Total: R$ {{ "%.2f"|format(total) }}</div>
      <form action="/checkout" method="POST">
        <button type="submit" class="btn-checkout">Finalizar Compra</button>
      </form>
    {% else %}
      <div class="empty-cart">
        Seu carrinho está vazio.<br><br>
        <a href="/">Voltar ao catálogo</a>
      </div>
    {% endif %}
  </div>
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
                emoji VARCHAR(10) DEFAULT '📦',
                category VARCHAR(50) DEFAULT 'Informática'
            )
        """)
        # Garante a coluna category em bancos já existentes
        cur.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'Informática'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                product_name VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]
        if count == 0:
            products = [
                ("Notebook Pro X", 4599.99, 15, "💻", "Informática"),
                ("Smartphone NordX", 2199.99, 42, "📱", "Acessórios"),
                ("Fone Bluetooth", 299.99, 80, "🎧", "Áudio"),
                ("Teclado Mecânico", 459.99, 30, "⌨️", "Periféricos"),
                ("Monitor 27\"", 1899.99, 12, "🖥️", "Informática"),
                ("Mouse Gamer", 189.99, 55, "🖱️", "Periféricos"),
            ]
            cur.executemany(
                "INSERT INTO products (name, price, stock, emoji, category) VALUES (%s, %s, %s, %s, %s)",
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

def get_cart_count():
    cart = session.get("cart", {})
    return sum(item["quantity"] for item in cart.values())

# ── Rotas ────────────────────────────────────────────────────
@app.route("/")
def index():
    hostname = socket.gethostname()
    zone = get_zone()
    mode = request.args.get("mode", "client")
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "Todos")
    sort_by = request.args.get("sort", "")
    products = []
    orders = []
    error = None
    db_status = "❌ Desconectado"
    flash_message = session.pop("flash_message", None)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = "SELECT id, name, price, stock, emoji, category FROM products WHERE 1=1"
        params = []

        if search_query:
            query += " AND name ILIKE %s"
            params.append(f"%{search_query}%")

        if selected_category and selected_category != "Todos":
            query += " AND category = %s"
            params.append(selected_category)

        if sort_by == "price_asc":
            query += " ORDER BY price ASC"
        elif sort_by == "price_desc":
            query += " ORDER BY price DESC"
        else:
            query += " ORDER BY id DESC"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        products = [
            {"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3], "emoji": r[4], "category": r[5]}
            for r in rows
        ]

        if mode == "admin":
            cur.execute("SELECT id, product_name, quantity, total, created_at FROM orders ORDER BY id DESC LIMIT 10")
            order_rows = cur.fetchall()
            orders = [
                {"id": r[0], "product_name": r[1], "quantity": r[2], "total": float(r[3]), "created_at": r[4].strftime("%d/%m %H:%M")}
                for r in order_rows
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
        orders=orders,
        error=error,
        mode=mode,
        search_query=search_query,
        categories=CATEGORIES,
        selected_category=selected_category,
        sort_by=sort_by,
        cart_count=get_cart_count(),
        flash_message=flash_message
    )

@app.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    emoji = request.form.get("emoji", "📦")
    category = request.form.get("category", "Informática")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, stock, emoji, category) VALUES (%s, %s, %s, %s, %s)",
            (name, float(price), int(stock), emoji, category)
        )
        conn.commit()
        cur.close()
        conn.close()
        session["flash_message"] = f"Produto '{name}' cadastrado com sucesso!"
    except Exception as e:
        print(f"Erro ao inserir: {e}")

    return redirect(url_for("index", mode="admin"))

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    quantity = int(request.form.get("quantity", 1))
    cart = session.get("cart", {})

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, price, emoji, stock FROM products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            name, price, emoji, stock = row
            key = str(product_id)
            current_qty = cart.get(key, {}).get("quantity", 0)
            new_qty = min(current_qty + quantity, stock)
            cart[key] = {
                "name": name,
                "price": float(price),
                "emoji": emoji,
                "quantity": new_qty
            }
            session["cart"] = cart
            session["flash_message"] = f"'{name}' adicionado ao carrinho!"
    except Exception as e:
        print(f"Erro ao adicionar ao carrinho: {e}")

    return redirect(url_for("index"))

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    items = [{"id": k, **v} for k, v in cart.items()]
    total = sum(item["quantity"] * item["price"] for item in items)
    return render_template_string(CART_HTML, items=items, total=total)

@app.route("/cart/remove/<product_id>", methods=["POST"])
def cart_remove(product_id):
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    return redirect(url_for("view_cart"))

@app.route("/checkout", methods=["POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("view_cart"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for product_id, item in cart.items():
            cur.execute(
                "UPDATE products SET stock = GREATEST(0, stock - %s) WHERE id = %s",
                (item["quantity"], int(product_id))
            )
            cur.execute(
                "INSERT INTO orders (product_name, quantity, total) VALUES (%s, %s, %s)",
                (item["name"], item["quantity"], item["quantity"] * item["price"])
            )
        conn.commit()
        cur.close()
        conn.close()
        session["flash_message"] = "Pedido finalizado com sucesso! Obrigado por comprar na NordMart."
    except Exception as e:
        print(f"Erro no checkout: {e}")

    session["cart"] = {}
    return redirect(url_for("index"))

@app.route("/delete/<int:product_id>")
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cur.close()
        conn.close()
        session["flash_message"] = "Produto excluído."
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