#!/bin/bash
set -e

echo "=== NordMart Deploy ==="

# Atualiza o sistema
apt-get update -y
apt-get install -y python3 python3-pip python3-venv

# Cria pasta da aplicação
mkdir -p /opt/nordmart
cp /tmp/app.py /opt/nordmart/app.py
cp /tmp/requirements.txt /opt/nordmart/requirements.txt

# Cria variáveis de ambiente
cat > /opt/nordmart/.env << EOF
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
EOF

# Instala dependências Python
cd /opt/nordmart
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Inicializa o banco
python3 -c "
import sys
sys.path.insert(0, '/opt/nordmart')
import os
os.environ['DB_HOST'] = '${DB_HOST}'
os.environ['DB_NAME'] = '${DB_NAME}'
os.environ['DB_USER'] = '${DB_USER}'
os.environ['DB_PASS'] = '${DB_PASS}'
from app import setup_database
setup_database()
print('Banco inicializado!')
"

# Cria serviço systemd para manter a aplicação rodando
cat > /etc/systemd/system/nordmart.service << EOF
[Unit]
Description=NordMart Flask App
After=network.target

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

echo "=== Deploy concluído! ==="