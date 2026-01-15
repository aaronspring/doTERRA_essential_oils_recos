# dōTERRA Essential Oils Discovery Engine

![Demo GIF showing discovery interactions](screenshots/demo.gif)

This project is a discovery-based recommendation engine for dōTERRA essential oils, powered by [Qdrant](https://qdrant.tech). 

Inspired by the [Qdrant Food Discovery Demo](https://github.com/qdrant/demo-food-discovery), this application allows users to explore a collection of essential oils not just through traditional keyword search, but by interacting with products and receiving recommendations based on their preferences.

## 🌟 Concept

Traditional search requires you to know exactly what you are looking for. However, when exploring essential oils, you might have a vague idea of a scent profile or a benefit but want to see options and explore related products.

This demo uses a **"Discovery" paradigm**:
1. You are presented with a set of oils. Optionally you can enter a search query to rank the oils related to your query.
2. You can **Like** or **Dislike** specific products.
3. The system uses Qdrant's [Recommendation API](https://qdrant.tech/documentation/concepts/search/#recommendation-api) to find other oils that are semantically similar to your likes and dissimilar to your dislikes.

## 🧠 Differences from Food Discovery

While inspired by the Food Discovery demo, there are key implementation differences:

- **Modality**: The Food Discovery demo uses **image-based** search (CLIP embeddings). This project focuses on **text-based** semantic search.
- **Embeddings**: We use the `jinaai/jina-embeddings-v2-base-de` model to generate embeddings from a "serialized" text representation of each oil (including its name, sub-name, description, and lifestyle benefits). Dieser Modell ist spezialisiert auf die deutsche Sprache und bietet eine exzellente semantische Repräsentation.
- **Data**: The dataset is custom-scraped from the dōTERRA website, containing detailed product information and high-quality product images.

## 🏗️ Architecture

The project consists of three main components:
- **Backend (FastAPI)**: Connects to Qdrant, handles vectorization of search queries, and exposes discovery/recommendation endpoints.
- **Frontend (React + Vite)**: A modern, responsive UI for browsing oils and interacting with the recommendation engine.
- **Qdrant**: The vector search engine that stores oil embeddings and metadata, performing high-performance similarity searches.

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js](https://nodejs.org/en/download)

---

### **🚀 Quick Start (One Command)**

If you have the prerequisites installed, you can set up the entire project (installing dependencies, starting the database, and processing data) and open the app with a single command:

```bash
make run-app
```

---


### 1. Project Setup

Install all dependencies using the unified `uv` environment:

```bash
make install
```

### 2. Start the Infrastructure

Run Qdrant and the Backend using Docker Compose:

```bash
make docker-up
```

### 3. Ingest Data

If you haven't already ingested the data into Qdrant, you can run the full pipeline or just the ingestion step:

```bash
# To run the full pipeline (scrape -> serialize -> ingest)
make pipeline

# Or just ingestion if you already have the CSVs
make ingest
```

### 4. Run the Frontend

The frontend is also managed via the Makefile:

```bash
make dev-frontend
```

Or run both backend and frontend together:

```bash
make dev
```

The application will be available at `http://localhost:5173`.

## 🛠️ Data Pipeline

If you want to update the data, the project includes several scraping scripts:
- `scrape_all.py`: Discovers all oil URLs from the dōTERRA sitemap.
- `scrape_single.py`: Scrapes detailed product information for each oil.
- `EDA.ipynb`: A Jupyter Notebook for exploratory data analysis of the collected data.

## ⚖️ Disclaimer

*This project is for demonstration purposes only. All product data and images belong to dōTERRA. This project is not affiliated with, endorsed by, or sponsored by dōTERRA.*
