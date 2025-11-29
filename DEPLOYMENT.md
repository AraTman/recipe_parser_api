# 🚀 Deployment Guide - Recipe Parser API

Bu rehber, Recipe Parser API'yi Coolify ile Ubuntu sunucuya nasıl deploy edeceğinizi adım adım anlatır.

## 📋 Gereksinimler

- Ubuntu 20.04+ sunucu
- En az 2GB RAM
- 20GB disk alanı
- Domain adı (opsiyonel ama önerilir)
- SSH erişimi

---

## 1️⃣ Sunucu Hazırlığı

### SSH ile Bağlan
```bash
ssh root@your-server-ip
```

### Sistem Güncellemesi
```bash
apt update && apt upgrade -y
```

### Docker Kurulumu
```bash
# Docker'ı kur
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose kur
apt install docker-compose -y

# Docker'ı test et
docker --version
docker-compose --version
```

### Firewall Ayarları
```bash
# UFW firewall kur ve yapılandır
apt install ufw -y

ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw allow 8000/tcp   # Coolify
ufw allow 8001/tcp   # Recipe API (geçici)
ufw allow 5678/tcp   # n8n (geçici)

ufw enable
ufw status
```

---

## 2️⃣ Coolify Kurulumu

### Coolify'ı Kur
```bash
# Tek komutla kurulum
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Kurulum tamamlandıktan sonra:
# http://your-server-ip:8000 adresinden erişin
```

### İlk Kurulum
1. Tarayıcıda `http://your-server-ip:8000` adresine git
2. İlk admin kullanıcısını oluştur
3. Email ve şifre belirle
4. Dashboard'a giriş yap

---

## 3️⃣ Lokal Test (Opsiyonel)

Sunucuya deploy etmeden önce lokal olarak test edin:

```bash
# Projeyi klonla
git clone https://github.com/your-username/recipe_parser_api.git
cd recipe_parser_api

# .env dosyası oluştur
cp .env.docker .env

# Docker Compose ile başlat
make up
# veya
docker-compose up -d

# Logları izle
make logs

# Test et
make test

# Durdur
make down
```

---

## 4️⃣ Coolify'da Deployment

### Yöntem 1: GitHub Repository ile (Önerilen)

#### 4.1. GitHub'a Push
```bash
# Projeyi GitHub'a push et
git add .
git commit -m "Add Docker configuration"
git push origin main
```

#### 4.2. Coolify'da Proje Oluştur
1. **Coolify Dashboard** → **+ New** → **Application**
2. **Source**: GitHub seç
3. **Repository**: `recipe_parser_api` seç
4. **Branch**: `main` seç
5. **Build Pack**: `Docker Compose` seç
6. **Port**: `8001` yaz

#### 4.3. Environment Variables Ekle
Coolify'da **Environment** sekmesine git ve ekle:

```bash
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=recipe_parser
OPENAI_API_KEY=your-key-here
ENABLE_AI_PARSING=false
PROXY_URL=
N8N_WEBHOOK_URL=http://n8n:5678/webhook/recipe-parsed
N8N_HOST=n8n.yourdomain.com
N8N_PROTOCOL=https
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-secure-password
TIMEZONE=Europe/Istanbul
```

#### 4.4. Deploy
1. **Deploy** butonuna tıkla
2. Build loglarını izle
3. Deployment tamamlandığında test et

### Yöntem 2: Manuel Docker Compose

```bash
# Sunucuda proje klasörü oluştur
mkdir -p /opt/recipe-parser-api
cd /opt/recipe-parser-api

# Dosyaları kopyala (SCP veya Git)
git clone https://github.com/your-username/recipe_parser_api.git .

# .env dosyası oluştur
cp .env.docker .env
nano .env  # Değerleri düzenle

# Başlat
docker-compose up -d

# Logları kontrol et
docker-compose logs -f
```

---

## 5️⃣ Domain ve SSL Ayarları

### DNS Ayarları
Domain sağlayıcınızda A record'ları ekleyin:

```
api.yourdomain.com    → your-server-ip
n8n.yourdomain.com    → your-server-ip
```

### Coolify'da Domain Ekle
1. **Application** → **Domains** sekmesi
2. **Add Domain**: `api.yourdomain.com` ekle
3. **SSL**: Otomatik Let's Encrypt aktif et
4. **Save**

n8n için aynı işlemi tekrarla: `n8n.yourdomain.com`

---

## 6️⃣ n8n Kurulumu ve Yapılandırma

### n8n'e Erişim
```
https://n8n.yourdomain.com
```

### İlk Giriş
- Username: `admin` (veya .env'de belirlediğiniz)
- Password: `.env`'deki şifre

### Örnek Workflow: Telegram Bot

1. **New Workflow** oluştur
2. **Telegram Trigger** node ekle
3. **HTTP Request** node ekle:
   - URL: `https://api.yourdomain.com/api/v1/parse-recipe`
   - Method: `POST`
   - Body: `{"url": "{{ $json.message.text }}"}`
4. **Telegram** node ekle (mesaj gönder)
5. **Save & Activate**

---

## 7️⃣ Monitoring ve Bakım

### Logları İzle
```bash
# Tüm servisler
docker-compose logs -f

# Sadece API
docker-compose logs -f recipe-api

# Sadece n8n
docker-compose logs -f n8n
```

### Container Durumu
```bash
docker-compose ps
docker stats
```

### MongoDB Backup
```bash
# Otomatik backup scripti
cat > /opt/backup-mongodb.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
docker exec recipe-mongodb mongodump --out=/backups/backup-$DATE
echo "Backup completed: $BACKUP_DIR/backup-$DATE"
EOF

chmod +x /opt/backup-mongodb.sh

# Cron job ekle (her gün 02:00)
crontab -e
# Ekle: 0 2 * * * /opt/backup-mongodb.sh
```

### Güncellemeler
```bash
# Kodu güncelle
cd /opt/recipe-parser-api
git pull

# Yeniden build ve başlat
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 8️⃣ Test ve Doğrulama

### Health Check
```bash
# API
curl https://api.yourdomain.com/health

# n8n
curl https://n8n.yourdomain.com/healthz
```

### Tarif Parse Testi
```bash
curl -X POST https://api.yourdomain.com/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DNX8U4tMR_P/"}'
```

### MongoDB Bağlantı Testi
```bash
docker exec -it recipe-mongodb mongosh
> use recipe_parser
> db.recipes.countDocuments()
> exit
```

---

## 9️⃣ Güvenlik Önerileri

### Firewall Sıkılaştırma
```bash
# Sadece Coolify ve SSH portlarını aç
ufw delete allow 8001/tcp
ufw delete allow 5678/tcp
ufw status
```

### MongoDB Authentication
```bash
# .env'e ekle
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=secure-password

# MONGODB_URL'i güncelle
MONGODB_URL=mongodb://admin:secure-password@mongodb:27017
```

### n8n Güvenlik
- Strong password kullan
- 2FA aktif et (n8n settings)
- Webhook URL'lerini gizli tut

### SSL/TLS
- Coolify otomatik Let's Encrypt kullanır
- Sertifika yenileme otomatik

---

## 🔟 Troubleshooting

### Problem: Container başlamıyor
```bash
# Logları kontrol et
docker-compose logs recipe-api

# Container'ı yeniden başlat
docker-compose restart recipe-api

# Tamamen yeniden başlat
docker-compose down
docker-compose up -d
```

### Problem: MongoDB bağlantı hatası
```bash
# MongoDB çalışıyor mu?
docker exec recipe-mongodb mongosh --eval "db.adminCommand('ping')"

# Network kontrolü
docker network inspect recipe_parser_api_recipe-network
```

### Problem: Port çakışması
```bash
# Portları kontrol et
netstat -tulpn | grep :8001
netstat -tulpn | grep :5678

# Çakışan servisi durdur veya docker-compose.yml'de portu değiştir
```

### Problem: Disk doldu
```bash
# Docker temizliği
docker system prune -a --volumes

# Eski backupları sil
rm -rf /backups/mongodb/backup-202311*
```

---

## 📊 Production Checklist

- [ ] Ubuntu sunucu hazır
- [ ] Docker ve Docker Compose kurulu
- [ ] Coolify kuruldu
- [ ] Firewall yapılandırıldı
- [ ] Domain DNS ayarları yapıldı
- [ ] SSL sertifikaları aktif
- [ ] Environment variables ayarlandı
- [ ] MongoDB backup scripti çalışıyor
- [ ] Monitoring kuruldu
- [ ] API test edildi
- [ ] n8n workflow'ları test edildi
- [ ] Güvenlik ayarları tamamlandı

---

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin: `docker-compose logs -f`
2. GitHub Issues açın
3. Dokümantasyonu inceleyin: [README.md](README.md)

---

**🎉 Başarılar! Recipe Parser API production'da çalışıyor!**
