# doTERRA Oil Data Extraction Pipeline

## Overview

This document describes the complete pipeline for extracting, validating, and enriching doTERRA essential oil product data from PDF Product Information Pages (PIPs).

## Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PDF EXTRACTION                                              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│     │  .pdf files │─▶│  paddleOCR  │─▶│  raw text output    │  │
│     │             │  │             │  │  (unstructured)     │  │
│     └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. PYDANTIC VALIDATION                                         │
│     ┌─────────────────────┐  ┌───────────────────────────────┐  │
│     │  unstructured text  │─▶│  PydanticOilProduct model     │  │
│     │                     │  │  (validation + normalization) │  │
│     └─────────────────────┘  └───────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. FILTERING                                                   │
│     ┌─────────────────────────┐  ┌───────────────────────────┐  │
│     │  all validated products │─▶│  filter to essential oils │  │
│     │                         │  │  only                    │  │
│     └─────────────────────────┘  └───────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. SHOP ENRICHMENT                                             │
│     ┌───────────────────────┐  ┌─────────────────────────────┐  │
│     │  filtered_oils.csv    │─▶│  Playwright MCP + manual    │  │
│     │                       │  │  shop_url + image_url       │  │
│     └───────────────────────┘  └─────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. OUTPUT                                                      │
│     ┌─────────────────────────────────────────────────────────┐  │
│     │  filtered_oils_with_shop_urls.csv                       │  │
│     │  - All oil data + shop_url + image_url + status        │  │
│     └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Stage 1: PDF Extraction with paddleOCR

### Purpose
Extract text from doTERRA Product Information Page (PIP) PDFs in German language.

### Technology
- **paddleOCR**: OCR engine for text extraction
- Supports German language (`lang="de"`)

### Code Example
```python
from paddleocr import PaddleOCR

def extract_text_from_pdf(pdf_path: str) -> str:
    ocr = PaddleOCR(lang="de", use_angle_cls=True)
    result = ocr.ocr(pdf_path, cls=True)
    
    extracted_text = ""
    for line in result[0]:
        extracted_text += line[1][0] + "\n"
    
    return extracted_text
```

### Input
- PDF files from `https://media.doterra.com/eu/de/pips/*.pdf`

### Output
- Raw unstructured text from each PDF

## Stage 2: Pydantic Data Validation

### Purpose
Parse unstructured OCR text into structured data models with validation.

### Pydantic Model
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ApplicationType(str, Enum):
    TOPICAL = "T"
    AROMATIC = "A"
    INTERNAL = "I"

class OilProduct(BaseModel):
    """Validated doTERRA oil product model"""
    url: str = Field(..., description="PDF URL")
    name: str = Field(..., description="Product name in German")
    latin_name: Optional[str] = Field(None, description="Latin botanical name")
    volume: Optional[str] = Field(None, description="Volume (e.g., '15 ml')")
    application: List[str] = Field(default_factory=list, description="Application types")
    plant_part: Optional[str] = Field(None, description="Plant part used")
    extraction_method: Optional[str] = Field(None, description="How oil is extracted")
    aroma_description: Optional[str] = Field(None, description="Scent profile")
    key_components: List[str] = Field(default_factory=list, description="Chemical compounds")
    primary_benefits: List[str] = Field(default_factory=list, description="Main benefits")
    product_description: str = Field("", description="Full product description")
    usage_instructions: List[str] = Field(default_factory=list, description="How to use")
    safety_notes: List[str] = Field(default_factory=list, description="Safety warnings")
    product_code: Optional[str] = Field(None, description="doTERRA SKU")
    language: str = Field(default="Deutsch", description="Language")

    class Config:
        json_encoders = {
            List: lambda v: str(v)
        }
```

### Parsing Strategy
The OCR output is parsed using regex patterns and heuristics:

```python
def parse_ocr_text(text: str) -> OilProduct:
    """Parse unstructured OCR text into OilProduct model"""
    
    # Extract name (usually first substantial line after URL)
    name = extract_name(text)
    
    # Extract Latin name
    latin_name = extract_latin_name(text)
    
    # Extract volume
    volume = extract_volume(text)
    
    # Extract application types
    application = extract_application_types(text)
    
    # Extract plant part
    plant_part = extract_plant_part(text)
    
    # Extract extraction method
    extraction_method = extract_extraction_method(text)
    
    # Extract aroma description
    aroma_description = extract_aroma(text)
    
    # Extract key chemical components
    key_components = extract_key_components(text)
    
    # Extract primary benefits
    primary_benefits = extract_benefits(text)
    
    # Extract full description
    product_description = extract_description(text)
    
    # Extract usage instructions
    usage_instructions = extract_usage(text)
    
    # Extract safety notes
    safety_notes = extract_safety(text)
    
    return OilProduct(
        url=extract_url(text),
        name=name,
        latin_name=latin_name,
        volume=volume,
        application=application,
        plant_part=plant_part,
        extraction_method=extraction_method,
        aroma_description=aroma_description,
        key_components=key_components,
        primary_benefits=primary_benefits,
        product_description=product_description,
        usage_instructions=usage_instructions,
        safety_notes=safety_notes
    )
```

### Error Handling
```python
class ExtractionError(Exception):
    """Raised when PDF extraction fails"""
    pass

def safe_extract(pdf_path: str) -> OilProduct:
    try:
        text = extract_text_from_pdf(pdf_path)
        product = parse_ocr_text(text)
        return product
    except Exception as e:
        # Log error and return partial data
        logger.error(f"Failed to extract {pdf_path}: {e}")
        return OilProduct(url=pdf_path, error=str(e))
```

## Stage 3: Filtering

### Purpose
Keep only essential oils, excluding supplements, personal care, etc.

### Filter Criteria
```python
def is_essential_oil(product: OilProduct) -> bool:
    """Filter to essential oil products only"""
    
    # Exclude known non-oil categories
    exclude_patterns = [
        "supplement", "capsule", "softgel", "vitamin",
        "serum", "toner", "lotion", "cream",
        "diffuser", "accessory", "kit", "collection"
    ]
    
    name_lower = product.name.lower()
    
    for pattern in exclude_patterns:
        if pattern in name_lower:
            return False
    
    return True
```

### Output
- `filtered_oils.csv`: 103 essential oil products

## Stage 4: Shop Enrichment

### Purpose
Add `shop_url` and `image_url` for each product.

### Methods
1. **Playwright MCP**: Automated browser navigation
2. **Manual verification**: For edge cases

### URL Correction Mapping
Some products have incorrect URLs that redirect or need correction:

```python
url_corrections = {
    "dōTERRA Balance™": {
        "wrong_url": "https://shop.doterra.com/de/de_de/shop/balance-oil/",
        "correct_url": "https://shop.doterra.com/de/de_de/shop/doterra-balance-oil/",
        "image_url": "https://prd-evo-content.doterra.com/.../balance-large-500x1350-eu.png"
    },
    "Whisper™ Mischung für Frauen": {
        "wrong_url": "https://shop.doterra.com/de/de_de/shop/whisper-oil/",
        "correct_url": "https://shop.doterra.com/DE/de_DE/shop/whisper-touch-oil/",
        "image_url": "https://prd-evo-content.doterra.com/.../whisper-touch-large-310x1350-eu.png"
    }
}
```

### Discontinued Products
Products that return HTTP 200 but show "Page Not Found" content:

```python
discontinued_products = {
    "Niaouli": "https://shop.doterra.com/de/de_de/shop/niaouli-oil/",
    "Yellow Mandarin (Gelbe Mandarine)": "https://shop.doterra.com/de/de_de/shop/yellow-mandarin-oil/",
    "HD Clear": "https://shop.doterra.com/de/de_de/shop/hd-clear-oil/",
    "Palmarosa": "https://shop.doterra.com/de/de_de/shop/palmarosa-oil/",
    "Smart & Sassy™ Aktiv-Mischung": "https://shop.doterra.com/de/de_de/shop/smart-sassy-oil/",
    "Ravintsara": "https://shop.doterra.com/de/de_de/shop/ravintsara-oil/"
}
```

### Playwright Extraction
```python
async def extract_shop_data(shop_url: str) -> dict:
    """Extract image URL from shop page using Playwright"""
    
    await page.goto(shop_url)
    await page.wait_for_load_state("networkidle")
    
    # Find product image
    images = await page.query_selector_all('img[src*="prd-evo-content.doterra.com"]')
    
    for img in images:
        src = await img.get_attribute("src")
        if "large" in src and "500x1350" in src:
            return {"image_url": src, "status": "OK_WITH_IMAGE"}
    
    return {"image_url": None, "status": "OK_NO_IMAGE"}
```

## Stage 5: Final Output

### File: `filtered_oils_with_shop_urls.csv`

#### Schema
| Column | Type | Description |
|--------|------|-------------|
| url | string | PDF URL |
| name | string | Product name |
| lateinischer_name | string | Latin botanical name |
| volumen | string | Volume |
| anwendung | list | Application types |
| pflanzenteil | string | Plant part |
| extraktionsmethode | string | Extraction method |
| aromabeschreibung | string | Aroma profile |
| hauptchemische_bestandteile | list | Key compounds |
| hauptnutzen | string | Benefits description |
| produktbeschreibung | string | Full description |
| anwendungsmoeglichkeiten | list | Usage instructions |
| hinweise_sichere_anwendung | list | Safety notes |
| produktcode | string | SKU |
| sprache | string | Language |
| error | string | Extraction error if any |
| latin_name | string | Latin name (duplicate) |
| hinweise_sichere_anwendung_list | string | Safety notes (list format) |
| hauptnutzen_list | string | Benefits (list format) |
| serialize | string | Serialized full description |
| shop_url | string | Product shop page URL |
| image_url | string | Product image URL |
| status | string | Status: OK_WITH_IMAGE, OK_NO_IMAGE, OK_WITH_IMAGE_CORRECTED, DISCONTINUED |

#### Status Values
- `OK_WITH_IMAGE`: Working product with valid image URL
- `OK_NO_IMAGE`: Working product, no image found
- `OK_WITH_IMAGE_CORRECTED`: URL was corrected, has image
- `DISCONTINUED`: Product discontinued (Page Not Found)

#### Statistics
| Metric | Count | Percentage |
|--------|-------|------------|
| Total products | 103 | 100% |
| With image_url | 96 | 93.2% |
| Working (no corrections) | 92 | 89.3% |
| URL corrected | 5 | 4.9% |
| Discontinued | 6 | 5.8% |

## Usage

### Reproduce Pipeline
```bash
# 1. Extract PDFs to CSV
python extract_pdfs.py

# 2. Validate with Pydantic
python validate_data.py

# 3. Filter to essential oils
python filter_oils.py

# 4. Enrich with shop data
python enrich_shop_data.py

# 5. Verify URLs
python verify_urls.py
```

### Query Data
```python
import csv

with open("filtered_oils_with_shop_urls.csv") as f:
    reader = csv.DictReader(f)
    oils = list(reader)

# Find all with images
with_images = [o for o in oils if o.get("image_url")]

# Find discontinued
discontinued = [o for o in oils if o.get("status") == "DISCONTINUED"]

# Find needing URL correction
corrected = [o for o in oils if o.get("status") == "OK_WITH_IMAGE_CORRECTED"]
```

## Dependencies
- `paddlepaddle` - OCR engine
- `paddleocr` - OCR wrapper
- `pydantic` - Data validation
- `playwright` - Browser automation
- `python-multipart` - Form handling

## Notes

1. **OCR Quality**: PDF quality affects extraction accuracy. Some products may have partial data.

2. **URL Stability**: doTERRA may change product URLs. The URL corrections in this pipeline reflect the current state as of 2026-02.

3. **Image URLs**: Image URLs follow pattern:
   - Single oils: `.../single-oils/{name}15ml-large-500x1350-eu.png`
   - Blends: `.../blends/{name}15ml-large-500x1350-eu.png`
   - Touch products: `.../{name}10ml-large-301x1350-eu.png`

4. **Language**: All data is in German (de_DE locale).
