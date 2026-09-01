#!/bin/bash
# ============================================
# Script de instalación para Oracle Cloud Free Tier
# Telegram English Tutor AI
# ============================================

set -e

echo "=========================================="
echo "  Telegram English Tutor AI - Setup VPS"
echo "=========================================="

# 1. Actualizar sistema
echo "[1/7] Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Docker
echo "[2/7] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker instalado. Cierra y vuelve a entrar para usar docker sin sudo."
fi

# 3. Instalar Docker Compose
echo "[3/7] Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 4. Instalar Git
echo "[4/7] Instalando Git..."
if ! command -v git &> /dev/null; then
    sudo apt install git -y
fi

# 5. Clonar repositorio
echo "[5/7] Clonando repositorio..."
cd /home/ubuntu
if [ ! -d "telegram-english-tutor" ]; then
    git clone https://github.com/JP-Romero/Telegram-English-Tutor.git telegram-english-tutor
fi
cd telegram-english-tutor

# 6. Crear archivo .env
echo "[6/7] Creando archivo .env..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Telegram Configuration
TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUI
WEBHOOK_URL=https://TU_IP_PUBLICA
SECRET_TOKEN=TU_SECRET_TOKEN

# Groq AI Configuration
GROQ_API_KEY=TU_GROQ_API_KEY

# Supabase Configuration
SUPABASE_URL=https://TU_SUPABASE_URL
SUPABASE_KEY=TU_SUPABASE_KEY

# App Configuration
DEBUG=False
PROJECT_NAME=Telegram English Tutor AI
VERSION=1.0.0
EOF
    echo "Archivo .env creado. Edítalo con tus datos reales:"
    echo "  nano /home/ubuntu/telegram-english-tutor/.env"
fi

# 7. Iniciar contenedor
echo "[7/7] Iniciando contenedor..."
docker-compose up -d --build

echo ""
echo "=========================================="
echo "  ¡Instalación completada!"
echo "=========================================="
echo ""
echo "Siguientes pasos:"
echo "1. Edita el archivo .env con tus datos:"
echo "   nano /home/ubuntu/telegram-english-tutor/.env"
echo ""
echo "2. Reinicia el contenedor:"
echo "   cd /home/ubuntu/telegram-english-tutor"
echo "   docker-compose restart"
echo ""
echo "3. Registra el webhook (desde tu computadora):"
echo "   curl -s 'https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://TU_IP/webhook&secret_token=TU_SECRET'"
echo ""
echo "4. Verifica que funcione:"
echo "   curl http://localhost:8000/health"
echo ""
