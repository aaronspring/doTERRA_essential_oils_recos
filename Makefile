.PHONY: help install scrape serialize ingest pipeline docker-up docker-down dev-backend dev-frontend dev

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies for all components"
	@echo "  make scrape        - Scrape raw data from dōTERRA sitemap"
	@echo "  make serialize     - Process and filter scraped data"
	@echo "  make ingest        - Generate embeddings and upload to Qdrant"
	@echo "  make pipeline      - Run scrape, serialize, and ingest in order"
	@echo "  make docker-up     - Start Qdrant and other services via docker-compose"
	@echo "  make docker-down   - Stop docker services"
	@echo "  make dev-backend   - Start backend development server"
	@echo "  make dev-frontend  - Start frontend development server"
	@echo "  make dev           - Start both backend and frontend"
	@echo "  make run-app       - Setup everything and open the app (One-click for anyone!)"

run-app: install docker-up
	@echo "Waiting for database to start..."
	@sleep 3
	@echo "Ensuring data is ingested..."
	make pipeline
	@echo "Starting the application..."
	@echo "Your browser will open automatically at http://localhost:5173"
	@open http://localhost:5173 || xdg-open http://localhost:5173 || echo "Please open http://localhost:5173 in your browser"
	make dev

install:
	@echo "Installing project dependencies with uv..."
	uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

scrape:
	uv run python processing/scrape_all.py

serialize:
	uv run python processing/serialize.py

ingest:
	uv run python processing/ingest_to_qdrant.py

pipeline: scrape serialize ingest

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

dev-backend:
	uv run uvicorn backend.main:app --reload

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend..."
	@echo "Use 'make dev-backend' and 'make dev-frontend' in separate terminals for full logs."
	(trap 'kill 0' SIGINT; make dev-backend & make dev-frontend)
