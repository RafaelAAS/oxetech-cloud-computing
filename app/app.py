import os
import socket
import psycopg2
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ── Configuração do banco ──────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "nordmart")
DB_USER = os.environ.get("DB_USER", "norddbadmin")
DB_PASS = os.environ.get("DB_PASS", "")

# ── Template HTML ──────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NordMart</title>
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
    }
    header h1 { font-size: 24px; letter-spacing: 2px; }
    header span {
      background: #e94560;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
    }
    .info-bar {
      background: #16213e;
      color: #aaa;
      text-align: center;
      padding: 8px;
      font-size: 12px;
    }
    .info-bar strong { color: #e94560; }
    .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
    h2 { margin-bottom: 20px; color: #1a1a2e; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 20px;
    }
    .card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      text-align: center;
    }
    .card .emoji { font-size: 40px; margin-bottom: 12px; }
    .card h3 { font-size: 16px; margin-bottom: 8px; }
    .card .price {
      color: #e94560;
      font-weight: bold;
      font-size: 18px;
    }
    .card .stock { color: #888; font-size: 12px; margin-top: 4px; }
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
      margin-top: 60px;
    }
  </style>
</head>
<body>
  <header>
    <h1>⬡ NORDMART</h1>
    <span>Cloud Lab — Azure</span>
  </header>

  <div class="info-bar">
    Servidor: <strong>{{ hostname }}</strong> &nbsp;|&nbsp;
    Zona: <strong>{{ zone }}</strong> &nbsp;|&nbsp;
    Banco: <strong>{{ db_status }}</strong>
  </div>

  <div class="container">
    <h2>Catálogo de Produtos</h2>

    {% if error %}
    <div class="error">
      <strong>⚠ Banco de dados indisponível</strong><br>
      {{ error }}
    </div>
    {% else %}
    <div class="grid">
      {% for product in products %}
      <div class="card">
        <div class="emoji">{{ product.emoji }}</div>
        <h3>{{ product.name }}</h3>
        <div class="price">R$ {{ "%.2f"|format(product.price) }}</div>
        <div class="stock">{{ product.stock }} em estoque</div>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <footer>
    NordMart &copy; 2024 — Infraestrutura Cloud Azure &nbsp;|&nbsp;
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
    """Cria a tabela e insere produtos de exemplo se não existirem."""
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
    """Tenta identificar a zona Azure via hostname."""
    hostname = socket.gethostname()
    if "vm-a" in hostname:
        return "Zone 1"
    elif "vm-b" in hostname:
        return "Zone 2"
    return "Unknown"

# ── Rotas ──────────────────────────────────────────────────────
@app.route("/")
def index():
    hostname = socket.gethostname()
    zone = get_zone()
    products = []
    error = None
    db_status = "❌ Desconectado"

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, price, stock, emoji FROM products ORDER BY id")
        rows = cur.fetchall()
        products = [
            {"name": r[0], "price": r[1], "stock": r[2], "emoji": r[3]}
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
        error=error
    )

@app.route("/health")
def health():
    """Endpoint usado pelo Load Balancer para verificar se a VM está viva."""
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