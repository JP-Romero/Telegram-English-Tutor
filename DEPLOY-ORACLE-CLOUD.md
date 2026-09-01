# Guía: Deploy Gratis en Oracle Cloud (1000+ usuarios)

## Paso 1: Crear cuenta en Oracle Cloud

1. Ve a https://cloud.oracle.com
2. Haz clic en **Start for Free**
3. Crea una cuenta con tu email
4. Verifica tu email y completa el registro
5. Selecciona **Region**: us-ashburn-1 (o la más cercana)
6. Agrega una tarjeta de crédito (no se cobra, es para verificar)

> ⚠️ Oracle Free Tier es **siempre gratis** para el tier ARM (4 CPU, 24GB RAM)

---

## Paso 2: Crear una VM Instance

1. En el Dashboard, ve a **Compute** → **Instances**
2. Haz clic en **Create Instance**
3. Configura:
   - **Name**: `telegram-tutor`
   - **Image**: Ubuntu 22.04 (o la más reciente)
   - **Shape**: **VM.Standard.A1.Flex** (ARM - GRATIS)
     - OCPUs: 4
     - Memory: 24 GB
   - **SSH Keys**: Sube tu clave pública SSH
     - Si no tienes: `ssh-keygen -t rsa` en tu terminal
     - Copia el contenido de `~/.ssh/id_rsa.pub`
4. Haz clic en **Create**

---

## Paso 3: Conectarte al servidor

```bash
# Cambia la IP por la de tu instancia
ssh -i ~/.ssh/id_rsa ubuntu@TU_IP_PUBLICA
```

---

## Paso 4: Instalar y configurar el bot

```bash
# Descargar el script de instalación
wget https://raw.githubusercontent.com/JP-Romero/Telegram-English-Tutor/main/setup-vps.sh

# Dar permisos de ejecución
chmod +x setup-vps.sh

# Ejecutar el script
./setup-vps.sh
```

---

## Paso 5: Configurar las variables de entorno

```bash
cd /home/ubuntu/telegram-english-tutor
nano .env
```

Reemplaza los valores:

```
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
WEBHOOK_URL=https://TU_IP_PUBLICA
SECRET_TOKEN=tu_secret_token
GROQ_API_KEY=tu_api_key_de_groq
SUPABASE_URL=https://tu_url.supabase.co
SUPABASE_KEY=tu_supabase_key
DEBUG=False
PROJECT_NAME=Telegram English Tutor AI
VERSION=1.0.0
```

Guarda con `Ctrl+X`, luego `Y`, luego `Enter`.

---

## Paso 6: Reiniciar el contenedor

```bash
docker-compose restart
```

---

## Paso 7: Registrar el webhook

Desde tu computadora local:

```bash
curl -s "https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://TU_IP/webhook&secret_token=TU_SECRET"
```

Deberías ver:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

---

## Paso 8: Verificar que funciona

```bash
curl http://TU_IP_PUBLICA/health
```

Deberías ver:
```json
{"status":"ok","project":"Telegram English Tutor AI"}
```

---

## Paso 9: Abrir el firewall

Si el bot no responde, abre el puerto 8000:

1. En Oracle Cloud, ve a **Networking** → **Virtual Cloud Networks**
2. Selecciona tu VCN
3. Ve a **Security Lists** → **Default Security List**
4. Haz clic en **Add Ingress Rules**
5. Configura:
   - **Source CIDR**: 0.0.0.0/0
   - **Destination Port**: 8000
6. Haz clic en **Add Ingress Rules**

---

## Paso 10: Probar el bot

1. Abre Telegram
2. Busca `@EchoEnglishTutorBot`
3. Envía `/start`
4. Prueba con texto, fotos y notas de voz

---

## Comandos útiles

```bash
# Ver logs del contenedor
docker-compose logs -f

# Reiniciar el bot
docker-compose restart

# Actualizar el bot
cd /home/ubuntu/telegram-english-tutor
git pull
docker-compose up -d --build

# Detener el bot
docker-compose down
```

---

## Solución de problemas

### El bot no responde
```bash
# Verificar que el contenedor está corriendo
docker-compose ps

# Ver logs
docker-compose logs --tail=50
```

### Error de webhook
```bash
# Verificar el webhook
curl -s "https://api.telegram.org/botTU_TOKEN/getWebhookInfo"

# Eliminar y volver a registrar
curl -s "https://api.telegram.org/botTU_TOKEN/deleteWebhook"
curl -s "https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://TU_IP/webhook&secret_token=TU_SECRET"
```

### El servidor no responde
1. Verifica que el puerto 8000 está abierto en Oracle Cloud
2. Verifica que el security list permite tráfico entrante
3. Reinicia la instancia desde Oracle Cloud

---

## Costo Total: $0/mes

Oracle Cloud Free Tier incluye:
- 4 OCPUs ARM (siempre gratis)
- 24 GB RAM (siempre gratis)
- 200 GB almacenamiento (siempre gratis)
- 10 TB de bandwidth (siempre gratis)

**No se cobra nada mientras uses el tier free.**
