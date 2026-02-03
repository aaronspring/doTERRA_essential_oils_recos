# Data Processing Pipeline

This directory contains the pipeline for scraping, processing, and ingesting dōTERRA essential oil data.

## Pipeline Execution Order

To update the dataset and vector database from scratch, run the scripts in the following order:

1.  **Scrape Data**:
    ```bash
    uv run python scrape_all.py
    # or: make scrape
    ```
    *   **Input**: doTERRA German sitemap.
    *   **Output**: `doterra_oils_sitemap.csv` (Raw scraped data).

2.  **Serialize & Filter Data**:
    ```bash
    uv run python serialize.py
    # or: make serialize
    ```
    *   **Input**: `doterra_oils_sitemap.csv`
    *   **Output**: `single_oil.csv` (Filtered for single oils with `serialized_text` column).
    *   This script handles categorization (Single vs Blend), filtering out base oils, and generating the text format used for embeddings.

3.  **Extract & Enrich Data**:
    ```bash
    uv run python run_extract_oils.py
    # or: make extract
    ```
    *   **Input**: `single_oil.csv`
    *   **Output**: `filtered_oils_with_shop_urls.csv` (Enriched oil data with shop URLs and descriptions).

4.  **Ingest to Qdrant**:
    ```bash
    uv run python ingest_to_qdrant.py
    # or: make ingest
    ```
    *   **Input**: `filtered_oils_with_shop_urls.csv`
    *   **Action**: Generates Jina embeddings (v2-base-de) and uploads them to the local Qdrant instance.
    *   **Note**: Ensure Qdrant is running via Docker (`docker-compose up -d`) before running this.

## Exploratory Data Analysis

*   **`EDA.ipynb`**: This Jupyter Notebook is used for exploratory analysis. It contains visualizations for sourcing locations, text length distributions, and product categorization logic. While the production pipeline logic has been moved to `serialize.py`, this notebook remains the primary tool for data discovery and validation.