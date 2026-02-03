.PHONY: help install scrape serialize ingest extract pipeline docker-up docker-down dev-backend dev-frontend dev lint typecheck format precommit

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies for all components"
	@echo "  make scrape        - Scrape raw data from dōTERRA sitemap"
	@echo "  make serialize     - Process and filter scraped data"
	@echo "  make extract       - Extract and enrich oil data from shop URLs"
	@echo "  make ingest        - Generate embeddings and upload to Qdrant"
	@echo "  make pipeline      - Run scrape, serialize, extract, and ingest in order"
	@echo "  See README.md for full pipeline details."
	@echo "  make docker-up     - Start Qdrant and other services via docker-compose"
	@echo "  make docker-down   - Stop docker services"
	@echo "  make dev-backend   - Start backend development server"
	@echo "  make dev-frontend  - Start frontend development server"
	@echo "  make dev           - Start both backend and frontend"
	@echo "  make run-app       - Setup everything and open the app (One-click for fresh system!)"
	@echo "  make run-app-no-scrape - Like run-app but skip the scraping step"
	@echo "  make format        - Format code with black, ruff and ty (via uvx)"
	@echo "  make precommit     - Run pre-commit hooks (via uvx)"

run-app: install docker-up
	@echo "Waiting for database to start..."
	@sleep 3
	@echo "Running full pipeline: scrape → serialize → extract → ingest..."
	make pipeline
	@echo "Starting the application..."
	@echo "Your browser will open automatically at http://localhost:5173"
	@open http://localhost:5173 || xdg-open http://localhost:5173 || echo "Please open http://localhost:5173 in your browser"
	make dev


run-app-no-scrape: install docker-up
	@echo "Waiting for database to start..."
	@sleep 3
	@echo "Skipping scraping step..."
	@echo "Ensuring data is ingested..."
	make ingest
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

extract:
	uv run python processing/run_extract_oils.py

ingest:
	uv run python processing/ingest_to_qdrant.py

pipeline: scrape serialize extract ingest

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

format:
	uvx black .
	uvx ruff check .
	uvx ty check .

precommit:
	uvx pre-commit run --all-files
