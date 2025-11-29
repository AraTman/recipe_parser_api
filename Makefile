# Recipe Parser API - Makefile
# Hızlı komutlar için

.PHONY: help build up down logs restart clean test

help: ## Yardım menüsü
	@echo "Recipe Parser API - Docker Komutları"
	@echo ""
	@echo "Kullanım: make [komut]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Docker image'ları build et
	docker-compose build

up: ## Servisleri başlat (detached mode)
	docker-compose up -d

down: ## Servisleri durdur
	docker-compose down

logs: ## Logları göster (tüm servisler)
	docker-compose logs -f

logs-api: ## Sadece API logları
	docker-compose logs -f recipe-api

logs-mongodb: ## Sadece MongoDB logları
	docker-compose logs -f mongodb

logs-n8n: ## Sadece n8n logları
	docker-compose logs -f n8n

restart: ## Servisleri yeniden başlat
	docker-compose restart

restart-api: ## Sadece API'yi yeniden başlat
	docker-compose restart recipe-api

clean: ## Container'ları ve volume'ları temizle
	docker-compose down -v
	docker system prune -f

clean-all: ## Tüm Docker verilerini temizle (DİKKAT: Veri kaybı!)
	docker-compose down -v
	docker system prune -af --volumes

ps: ## Çalışan container'ları listele
	docker-compose ps

shell-api: ## API container'ına shell aç
	docker exec -it recipe-parser-api /bin/bash

shell-mongodb: ## MongoDB shell aç
	docker exec -it recipe-mongodb mongosh

shell-n8n: ## n8n container'ına shell aç
	docker exec -it recipe-n8n /bin/sh

test: ## API'yi test et
	curl -f http://localhost:8001/health || echo "API çalışmıyor!"
	curl -f http://localhost:5678/healthz || echo "n8n çalışmıyor!"

test-parse: ## Örnek tarif parse testi
	curl -X POST http://localhost:8001/api/v1/parse-recipe \
		-H "Content-Type: application/json" \
		-d '{"url": "https://www.instagram.com/reel/DNX8U4tMR_P/"}'

backup-mongodb: ## MongoDB backup al
	docker exec recipe-mongodb mongodump --out=/backups/backup-$$(date +%Y%m%d-%H%M%S)

restore-mongodb: ## MongoDB restore et (BACKUP_DIR gerekli)
	@if [ -z "$(BACKUP_DIR)" ]; then \
		echo "Kullanım: make restore-mongodb BACKUP_DIR=/backups/backup-20231201-120000"; \
		exit 1; \
	fi
	docker exec recipe-mongodb mongorestore $(BACKUP_DIR)

stats: ## Container istatistikleri
	docker stats recipe-parser-api recipe-mongodb recipe-n8n

# Production komutları
prod-up: ## Production modda başlat
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Production modda durdur
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Production logları
	docker-compose -f docker-compose.prod.yml logs -f

prod-build: ## Production build
	docker-compose -f docker-compose.prod.yml build --no-cache

# Development komutları
dev-setup: ## Development ortamı kur
	cp .env.docker .env
	@echo "✅ .env dosyası oluşturuldu"
	@echo "📝 .env dosyasını düzenleyin ve 'make up' komutunu çalıştırın"

dev-test: ## Test scriptini çalıştır
	python test_production_api.py

# Monitoring
monitor: ## Tüm servislerin durumunu izle
	watch -n 2 'docker-compose ps && echo "" && docker stats --no-stream recipe-parser-api recipe-mongodb recipe-n8n'
