#!/bin/bash

# ==========================================
# Django Education System - Auto Deploy Script
# ==========================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="edu_system"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "لا تشغل السكريبت كـ root! استخدم: bash deploy.sh"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "التحقق من المتطلبات..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker غير مثبت! قم بتثبيته أولاً: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose غير مثبت!"
        exit 1
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        print_warning "ملف .env غير موجود! سيتم إنشاء نموذج..."
        cat > .env << 'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=change-this-to-a-secure-key-$(openssl rand -base64 50)
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Settings (Brevo)
EMAIL_HOST_USER=your-email@smtp-brevo.com
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=your-email@example.com
EOF
        print_error "قم بتحديث ملف .env بإعداداتك ثم أعد تشغيل السكريبت"
        exit 1
    fi
    
    # Check SSL certificates
    if [ ! -f cert.crt ] || [ ! -f cert.key ]; then
        print_warning "شهادات SSL غير موجودة! إنشاء شهادة self-signed..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout cert.key -out cert.crt \
            -subj "/C=EG/ST=Cairo/L=Cairo/O=Education/CN=localhost" \
            2>/dev/null
        print_warning "تم إنشاء شهادة مؤقتة. للإنتاج، استخدم Let's Encrypt!"
    fi
    
    print_success "جميع المتطلبات متوفرة!"
}

# Build and deploy
build_and_deploy() {
    print_status "بناء Docker images..."
    docker compose build --no-cache
    
    print_status "إيقاف الخدمات القديمة..."
    docker compose down --remove-orphans 2>/dev/null || true
    
    print_status "تشغيل الخدمات..."
    docker compose up -d
    
    print_status "انتظار readiness..."
    sleep 10
    
    # Health check
    print_status "فحص صحة التطبيق..."
    for i in {1..10}; do
        if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
            print_success "التطبيق يعمل بشكل صحيح!"
            return 0
        fi
        echo -n "."
        sleep 3
    done
    
    print_error "فشل فحص الصحة! تحقق من اللوجات: docker compose logs"
    return 1
}

# Show info
show_info() {
    echo ""
    echo "=========================================="
    print_success "تم النشر بنجاح! 🎉"
    echo "=========================================="
    echo ""
    echo -e "الموقع: ${GREEN}https://localhost${NC} (أو دومينك)"
    echo -e "الإدارة: ${GREEN}https://localhost/admin${NC}"
    echo -e "Health Check: ${GREEN}http://localhost:8000/health/${NC}"
    echo ""
    echo -e "لمراقبة اللوجات: ${YELLOW}docker compose logs -f${NC}"
    echo -e "لإنشاء superuser: ${YELLOW}docker compose exec web python manage.py createsuperuser${NC}"
    echo ""
}

# Main
main() {
    echo "=========================================="
    echo "  Django Education System - Deploy Script"
    echo "=========================================="
    echo ""
    
    check_root
    check_prerequisites
    build_and_deploy
    show_info
}

# Run
main "$@"
