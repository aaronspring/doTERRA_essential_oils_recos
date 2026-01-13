# dōTERRA Essential Oils Discovery Engine

This project is a discovery-based recommendation engine for dōTERRA essential oils, powered by [Qdrant](https://qdrant.tech). 

Inspired by the [Qdrant Food Discovery Demo](https://github.com/qdrant/demo-food-discovery), this application allows users to explore a collection of essential oils not just through traditional keyword search, but by interacting with products and receiving recommendations based on their preferences.

## 🌟 Concept

Traditional search requires you to know exactly what you are looking for. However, when exploring essential oils, you might have a vague idea of a scent profile or a benefit but want to see options and explore related products.

This demo uses a **"Discovery" paradigm**:
1. You are presented with a set of oils.
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
- Python 3.10+ (for data ingestion)
- Node.js (for running the frontend locally)

### 1. Start the Infrastructure

Run Qdrant and the Backend using Docker Compose:

```bash
docker-compose up -d
```

### 2. Ingest Data

First, install the backend dependencies locally to run the ingestion script:

```bash
# Recommended to use a virtual environment
pip install pandas sentence-transformers qdrant-client tqdm torch
```

Then, run the ingestion script to vectorize the oils and upload them to Qdrant:

```bash
python ingest_to_qdrant.py
```

*Note: Ensure `single_oil.csv` or `doterra_oils_serialized.csv` is present in the root directory.*

### 3. Run the Frontend

Navigate to the frontend directory and start the development server:

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:5173`.

## 🛠️ Data Pipeline

If you want to update the data, the project includes several scraping scripts:
- `scrape_all.py`: Discovers all oil URLs from the dōTERRA sitemap.
- `scrape_single.py`: Scrapes detailed product information for each oil.
- `EDA.ipynb`: A Jupyter Notebook for exploratory data analysis of the collected data.

## ⚖️ Disclaimer

*This project is for demonstration purposes only. All product data and images belong to dōTERRA. This project is not affiliated with, endorsed by, or sponsored by dōTERRA.*
