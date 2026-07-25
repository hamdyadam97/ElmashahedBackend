# دليل النشر على VPS باستخدام Docker

## 📋 متطلبات النظام

- VPS بمواصفات: 2 CPU / 4GB RAM (مقترحة)
- Ubuntu 22.04 LTS (أو أي توزيعة Linux حديثة)
- Docker & Docker Compose
- دومين (Domain) - اختياري لكن مستحسن

---

## 🚀 خطوات النشر

### 1. تجهيز الـ VPS

اتصل بالـ VPS عبر SSH:
```bash
ssh root@YOUR_SERVER_IP
```

تحديث النظام:
```bash
sudo apt update && sudo apt upgrade -y
```

تثبيت Docker:
```bash
# تثبيت Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# إضافة المستخدم لمجموعة docker
sudo usermod -aG docker $USER
newgrp docker

# تثبيت Docker Compose
sudo apt install docker-compose-plugin -y
```

---

### 2. نسخ المشروع للـ VPS

#### الطريقة الأولى: Git Clone
```bash
cd /opt
sudo git clone https://github.com/yourusername/edu_system.git
sudo chown -R $USER:$USER edu_system
cd edu_system
```

#### الطريقة الثانية: نسخ الملفات يدوياً
```bash
# من جهازك المحلي
scp -r . root@YOUR_SERVER_IP:/opt/edu_system

# على الـ VPS
cd /opt/edu_system
```

---

### 3. إعداد ملف البيئة (.env)

```bash
nano .env
```

أضف الإعدادات التالية:
```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-change-this
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database (SQLite - للبساطة)
# أو PostgreSQL لو حابب:
# DATABASE_URL=postgresql://user:password@db:5432/edu_system

# Email Settings
EMAIL_HOST_USER=your-email@smtp-brevo.com
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

⚠️ **تنبيه:** تأكد من تغيير `SECRET_KEY` باستخدام:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

### 4. إعداد شهادة SSL (اختياري لكن مستحسن)

#### باستخدام Let's Encrypt (مجاني):
```bash
# تثبيت Certbot
sudo apt install certbot -y

# الحصول على شهادة
sudo certbot certonly --standalone -d your-domain.com

# نسخ الشهادات
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./cert.key

# تعديل الصلاحيات
sudo chown $USER:$USER cert.crt cert.key
chmod 600 cert.key
```

#### أو استخدم شهادة self-signed مؤقتاً:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout cert.key -out cert.crt \
  -subj "/C=EG/ST=Cairo/L=Cairo/O=Education/CN=your-domain.com"
```

---

### 5. بناء وتشغيل Docker Containers

```bash
# بناء الصور
docker compose build

# تشغيل الخدمات
docker compose up -d

# مشاهدة اللوجات
docker compose logs -f
```

---

### 6. إنشاء Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

---

### 7. التحقق من النشر

افتح المتصفح وانتقل إلى:
- `https://your-domain.com` - الموقع
- `https://your-domain.com/admin` - لوحة التحكم
- `https://your-domain.com/health/` - Health check

---

## 🔄 إدارة المشروع

### إيقاف الخدمات:
```bash
docker compose down
```

### إعادة تشغيل:
```bash
docker compose restart
```

### تحديث المشروع:
```bash
# سحب التحديثات
git pull

# إعادة البناء والتشغيل
docker compose down
docker compose build --no-cache
docker compose up -d
```

### مشاهدة اللوجات:
```bash
# كل الخدمات
docker compose logs -f

# خدمة معينة
docker compose logs -f web

# آخر 100 سطر
docker compose logs --tail 100 web
```

### النسخ الاحتياطي:
```bash
# نسخ قاعدة البيانات
docker compose exec web python manage.py dumpdata > backup.json

# نسخ ملفات الميديا
tar -czvf media_backup.tar.gz media/

# نسخ قاعدة البيانات SQLite
sudo cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

---

## 🛡️ الأمان

### 1. جدار الحماية (UFW)
```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban (منع الهجمات)
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

### 3. تحديث تلقائي
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure unattended-upgrades
```

---

## 📊 مراقبة الأداء

### استخدام الموارد:
```bash
docker stats
```

### تنظيف Docker:
```bash
# حذف الصور الغير مستخدمة
docker image prune -a

# حذف الحاويات المتوقفة
docker container prune

# حذف الفوليومز الغير مستخدمة
docker volume prune
```

---

## 🆘 استكشاف الأخطاء

### المشكلة: الخدمة لا تعمل
```bash
# التحقق من حالة الحاويات
docker compose ps

# مشاهدة اللوجات
docker compose logs web

# الدخول للحاوية
docker compose exec web sh
```

### المشكلة: قاعدة البيانات
```bash
# إعادة تشغيل migrations
docker compose exec web python manage.py migrate --run-syncdb

# التحقق من الاتصال
docker compose exec web python manage.py dbshell
```

### المشكلة: Static files
```bash
# إعادة جمع الملفات
docker compose exec web python manage.py collectstatic --noinput --clear
```

---

## 📞 الدعم

في حالة وجود مشاكل، تأكد من:
1. ✅ ملف `.env` صحيح وكامل
2. ✅ الشهادات موجودة (cert.crt, cert.key)
3. ✅ المنافح 80 و 443 مفتوحة في جدار الحماية
4. ✅ Docker و Docker Compose يعملان بشكل صحيح

---

تم التطوير ب❤️ بواسطة فريق التعليم
