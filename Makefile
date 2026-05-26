.PHONY: up down backend frontend install db-init logs

# ── Levantar entorno completo ──────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# ── Desarrollo local sin Docker ────────────────────────────────────────────
backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# ── Instalación local ──────────────────────────────────────────────────────
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ── Base de datos local ────────────────────────────────────────────────────
db-init:
	psql -U postgres -d network_audit_db -f backend/migrations/001_initial_schema.sql

db-create:
	createdb -U postgres network_audit_db

# ── Setup inicial completo (local sin Docker) ──────────────────────────────
setup: install db-create db-init
	cp backend/.env.example backend/.env
	@echo ""
	@echo "✅ Setup completo."
	@echo "   Edita backend/.env si necesitas ajustar la conexión a PostgreSQL."
	@echo ""
	@echo "   Para iniciar:"
	@echo "     Terminal 1: make backend"
	@echo "     Terminal 2: make frontend"
	@echo ""
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   Frontend: http://localhost:5173/network-audit"
