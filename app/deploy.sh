#!/bin/bash
set -e

echo "=== NordMart Deploy (Local PostgreSQL) ==="

# Atualiza o sistema e instala Python + PostgreSQL local
apt-get update -y
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib

# Inicia e habilita o serviço do Postgres
systemctl start postgresql
systemctl enable postgresql

# Configura o usuário e o banco de dados localmente
sudo -u postgres psql -c "CREATE USER norddbadmin WITH PASSWORD 'NordMart@2024!';" || true
sudo -u postgres psql -c "CREATE DATABASE nordmart OWNER norddbadmin;" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nordmart TO norddbadmin;" || true

# Cria pasta da aplicação
mkdir -p /opt/nordmart
cp /tmp/app.py /opt/nordmart/app.py
cp /tmp/requirements.txt /opt/nordmart/requirements.txt

# Como o banco roda na própria máquina, o DB_HOST é localhost
cat << EOF > /opt/nordmart/.env
DB_HOST=localhost
DB_NAME=nordmart
DB_USER=norddbadmin
DB_PASS=NordMart@2024!
EOF

# Instala dependências Python
cd /opt/nordmart
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Inicializa o banco de dados (tabela e produtos)
python3 -c "
import sys
sys.path.insert(0, '/opt/nordmart')
import os
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'nordmart'
os.environ['DB_USER'] = 'norddbadmin'
os.environ['DB_PASS'] = 'NordMart@2024!'
from app import setup_database
setup_database()
print('Banco local inicializado com sucesso!')
"

# Cria serviço systemd para manter a aplicação Flask rodando
cat << EOF > /etc/systemd/system/nordmart.service
[Unit]
Description=NordMart Flask App
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/nordmart
EnvironmentFile=/opt/nordmart/.env
ExecStart=/opt/nordmart/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:80 app:app
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nordmart
systemctl restart nordmart

echo "=== Deploy concluído com sucesso! ==="