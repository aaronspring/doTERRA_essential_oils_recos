#!/usr/bin/env python3
"""
Essential Oil Document Extractor - Simplified Version
Uses PaddleOCR-VL-1.5 for OCR and LLM structured output for extraction.
"""

import argparse
import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from paddleocr import PaddleOCRVL
from pdf2image import convert_from_path
from pydantic import BaseModel, Field, field_validator

DEFAULT_MODEL = "ministral-3:3b"
OPENAI_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-5-mini",
}
OLLAMA_MODELS = {"ministral-3:3b"}


# =============================================================================
# Pydantic Models
# =============================================================================


class EssentialOil(BaseModel):
    """English model for essential oil product information."""

    name: str = Field(default="", description="Product name (e.g., Wild Orange)")
    latin_name: str = Field(default="", description="Scientific/Latin name (e.g., Citrus sinensis)")
    volume: str | None = Field(default=None, description="Volume (e.g., 15 mL)")
    application: list[str] = Field(
        default_factory=list,
        description="Application methods (A=Aromatic, T=Topical, I=Internal, N=Neat)",
    )
    plant_part: list[str] = Field(default_factory=list, description="Plant part used")
    extraction_method: str = Field(default="", description="Extraction method")
    aroma_description: list[str] = Field(default_factory=list, description="Aroma characteristics")
    main_chemical_constituents: list[str] = Field(
        default_factory=list, description="Main chemical components"
    )
    primary_benefits: list[str] = Field(default_factory=list, description="Primary health benefits")
    product_description: str = Field(default="", description="Full product description")
    uses: list[str] = Field(default_factory=list, description="Suggested uses")
    directions_for_use: list[str] = Field(default_factory=list, description="Usage directions")
    cautions: list[str] = Field(default_factory=list, description="Safety cautions")
    product_code: str | None = Field(default=None, description="Product code/SKU")
    language: str = Field(default="en", description="Document language")

    @field_validator(
        "name", "latin_name", "extraction_method", "product_description", mode="before"
    )
    @classmethod
    def coerce_to_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator(
        "application",
        "plant_part",
        "aroma_description",
        "main_chemical_constituents",
        "primary_benefits",
        "uses",
        "directions_for_use",
        "cautions",
        mode="before",
    )
    @classmethod
    def empty_list_if_none(cls, v):
        return v if v is not None else []


class DeutschesAetherischesOel(BaseModel):
    """German model for essential oil product information."""

    name: str = Field(default="", description="Produktname (z.B. Tangerine)")
    lateinischer_name: str = Field(
        default="", description="Wissenschaftlicher Name (z.B. Citrus reticulata)"
    )
    volumen: str | None = Field(default=None, description="Volumen (z.B. 15 mL)")
    anwendung: list[str] = Field(
        default_factory=list,
        description="Anwendungsmethoden (A=Aromatisch, T=Topisch, I=Innerlich, N=Pur)",
    )
    pflanzenteil: list[str] = Field(default_factory=list, description="Verwendeter Pflanzenteil")
    extraktionsmethode: str = Field(default="", description="Extraktionsmethode")
    aromabeschreibung: list[str] = Field(default_factory=list, description="Aroma-Eigenschaften")
    hauptchemische_bestandteile: list[str] = Field(
        default_factory=list, description="Hauptchemische Bestandteile"
    )
    hauptnutzen: list[str] = Field(default_factory=list, description="Hauptnutzen/Vorteile")
    produktbeschreibung: str = Field(default="", description="Vollständige Produktbeschreibung")
    anwendungsmoeglichkeiten: list[str] = Field(
        default_factory=list, description="Anwendungsmöglichkeiten"
    )
    hinweise_sichere_anwendung: list[str] = Field(
        default_factory=list,
        description="Hinweise zur sicheren Anwendung (Vorsichtsmaßnahmen, Warnhinweise)",
    )
    produktcode: str | None = Field(default=None, description="Produktcode/SKU")
    sprache: str = Field(default="de", description="Dokumentensprache")

    @field_validator(
        "name",
        "lateinischer_name",
        "extraktionsmethode",
        "produktbeschreibung",
        mode="before",
    )
    @classmethod
    def coerce_to_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator(
        "anwendung",
        "pflanzenteil",
        "aromabeschreibung",
        "hauptchemische_bestandteile",
        "hauptnutzen",
        "anwendungsmoeglichkeiten",
        "hinweise_sichere_anwendung",
        mode="before",
    )
    @classmethod
    def empty_list_if_none(cls, v):
        return v if v is not None else []

    def to_essential_oil(self) -> EssentialOil:
        """Convert German model to English model."""
        return EssentialOil(
            name=self.name,
            latin_name=self.lateinischer_name,
            volume=self.volumen,
            application=self.anwendung,
            plant_part=self.pflanzenteil,
            extraction_method=self.extraktionsmethode,
            aroma_description=self.aromabeschreibung,
            main_chemical_constituents=self.hauptchemische_bestandteile,
            primary_benefits=self.hauptnutzen,
            product_description=self.produktbeschreibung,
            uses=self.anwendungsmoeglichkeiten,
            directions_for_use=[],
            cautions=self.hinweise_sichere_anwendung,
            product_code=self.produktcode,
            language=self.sprache,
        )


# =============================================================================
# OCR and Utilities
# =============================================================================

_pipeline = None
_llm = None
_current_model = None


def get_pipeline() -> PaddleOCRVL:
    """Get or initialize PaddleOCR-VL-1.5 pipeline."""
    global _pipeline
    if _pipeline is None:
        print("Initializing PaddleOCR-VL-1.5...")
        _pipeline = PaddleOCRVL(
            vl_rec_backend="mlx-vlm-server",
            vl_rec_server_url="http://localhost:8111/",
            vl_rec_api_model_name="PaddlePaddle/PaddleOCR-VL-1.5",
        )
    return _pipeline


def get_llm(model: str = DEFAULT_MODEL) -> BaseChatModel:
    """Get or initialize LLM for structured extraction."""
    global _llm, _current_model

    if _llm is not None and _current_model == model:
        return _llm

    if model in OPENAI_MODELS:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(f"OPENAI_API_KEY environment variable required for model '{model}'")
        from langchain_openai import ChatOpenAI

        _llm = ChatOpenAI(model=model, temperature=0)
    else:
        _llm = ChatOllama(model=model, temperature=0)

    _current_model = model
    return _llm


def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def download_file(url: str, dest_path: str) -> str:
    urllib.request.urlretrieve(url, dest_path)
    return dest_path


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> list[str]:
    """Convert PDF pages to images (max 2 pages)."""
    poppler_paths = ["/opt/homebrew/bin/", "/usr/local/bin/", "/usr/bin/", None]
    pages = None

    for poppler_path in poppler_paths:
        try:
            if poppler_path and os.path.exists(poppler_path):
                pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
            else:
                pages = convert_from_path(pdf_path, dpi=dpi)
            break
        except Exception:
            continue

    if pages is None:
        raise RuntimeError("Failed to convert PDF - poppler not found")

    if len(pages) > 2:
        raise ValueError(f"PDF has {len(pages)} pages. Only 1-2 pages supported.")

    temp_dir = tempfile.gettempdir()
    image_paths = []

    for i, page in enumerate(pages):
        temp_image_path = os.path.join(temp_dir, f"pdf_page_{i}_{os.path.basename(pdf_path)}.png")
        page.save(temp_image_path, "PNG")
        image_paths.append(temp_image_path)
        print(f"Converted page {i + 1} to: {temp_image_path}")

    return image_paths


def prepare_images(input_path: str) -> tuple[list[str], list[str]]:
    """Prepare images from file path or URL."""
    cleanup_files = []

    if is_url(input_path):
        print(f"Downloading from URL: {input_path}")
        parsed_url = urllib.parse.urlparse(input_path)
        url_filename = os.path.basename(parsed_url.path) or "downloaded.pdf"
        temp_dir = tempfile.gettempdir()
        downloaded_file = os.path.join(temp_dir, url_filename)
        download_file(input_path, downloaded_file)
        print(f"Downloaded to: {downloaded_file}")
        cleanup_files.append(downloaded_file)
        input_path = downloaded_file

    if input_path.lower().endswith(".pdf"):
        print(f"Converting PDF: {input_path}")
        image_paths = convert_pdf_to_images(input_path)
        cleanup_files.extend(image_paths)
    else:
        image_paths = [input_path]

    return image_paths, cleanup_files


def ocr_to_text(image_path: str) -> str:
    """Run OCR on image and return combined text."""
    pipeline = get_pipeline()
    output = pipeline.predict(input=image_path)
    pages = list(output)

    if not pages:
        return ""

    page = pages[0]
    parsing_results = page.get("parsing_res_list", [])
    texts = [getattr(res, "content", "") for res in parsing_results]
    return "\n".join(texts)


def detect_language(text: str) -> str:
    """Detect if text is German or English."""
    text_lower = text.lower()
    german_keywords = [
        "produktbeschreibung",
        "anwendung",
        "vorsichtsmaßnahmen",
        "vorteile",
        "ätherisches öl",
        "pflanzenteil",
        "extraktionsmethode",
    ]
    english_keywords = [
        "product description",
        "application",
        "cautions",
        "benefits",
        "essential oil",
        "plant part",
        "extraction method",
    ]

    german_score = sum(1 for kw in german_keywords if kw in text_lower)
    english_score = sum(1 for kw in english_keywords if kw in text_lower)

    return "de" if german_score > english_score else "en"


# =============================================================================
# LLM-based Structured Extraction
# =============================================================================

SYSTEM_PROMPT_EN = """You are an expert at extracting structured product information from essential oil documents.
Extract all available information from the OCR text into the specified JSON schema.

Rules:
- Extract EXACTLY what is in the text, do not invent information
- If a field is not present in the text, use null for optional fields or empty string/list for required fields
- For application methods, look for letters like A (Aromatic), T (Topical), I (Internal), N (Neat)
- Split comma-separated values into list items
- Remove bullet points and formatting from list items
- The product code is usually a 7+ digit number"""

SYSTEM_PROMPT_DE = """Du bist ein Experte für die Extraktion strukturierter Produktinformationen aus Dokumenten zu ätherischen Ölen.
Extrahiere alle verfügbaren Informationen aus dem OCR-Text in das angegebene JSON-Schema.

Regeln:
- Extrahiere GENAU das, was im Text steht, erfinde keine Informationen
- Wenn ein Feld nicht im Text vorhanden ist, verwende null für optionale Felder oder leere Zeichenfolge/Liste für erforderliche Felder
- Für Anwendungsmethoden suche nach Buchstaben wie A (Aromatisch), T (Topisch), I (Innerlich), N (Pur)
- Teile kommagetrennte Werte in Listenelemente auf
- Entferne Aufzählungszeichen und Formatierungen aus Listenelementen
- Der Produktcode ist normalerweise eine 7+ stellige Zahl"""


def extract_structured(
    text: str, language: str, model: str = DEFAULT_MODEL
) -> EssentialOil | DeutschesAetherischesOel:
    """Extract structured data from OCR text using LLM."""
    llm = get_llm(model)

    if language == "de":
        schema = DeutschesAetherischesOel
        system_prompt = SYSTEM_PROMPT_DE
    else:
        schema = EssentialOil
        system_prompt = SYSTEM_PROMPT_EN

    structured_llm = llm.with_structured_output(schema)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Extract from this OCR text:\n\n{doc_text}"),
        ]
    )

    chain = prompt | structured_llm
    result = chain.invoke({"doc_text": text})

    return result


# =============================================================================
# Main Extraction Pipeline
# =============================================================================


def extract_from_images(
    image_paths: list[str], output_format: str = "auto", model: str = DEFAULT_MODEL
) -> dict:
    """Extract essential oil data from images."""
    print(f"\n{'=' * 70}")
    print("EXTRACTING ESSENTIAL OIL DATA")
    print(f"{'=' * 70}")
    print(f"Processing {len(image_paths)} page(s)\n")

    # Combine OCR text from all pages
    all_text = []
    for i, image_path in enumerate(image_paths, 1):
        print(f"--- Page {i}: OCR ---")
        text = ocr_to_text(image_path)
        all_text.append(text)
        print(f"Extracted {len(text)} characters")

    combined_text = "\n\n".join(all_text)

    # Detect language
    language = detect_language(combined_text)
    print(f"\nDetected language: {language}")

    # Determine output format
    if output_format == "auto":
        output_format = language

    # Extract structured data
    print(f"Extracting with LLM '{model}' ({output_format} schema)...")
    result = extract_structured(combined_text, output_format, model)

    return result.model_dump()


def main():
    parser = argparse.ArgumentParser(description="Extract essential oil information")
    parser.add_argument(
        "input_path",
        nargs="?",
        default="wild_orange.png",
        help="Path to image, PDF, or URL",
    )
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument(
        "-f",
        "--output-format",
        choices=["en", "de", "auto"],
        default="auto",
        help="Output format",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model for extraction (default: {DEFAULT_MODEL}). "
        f"Ollama models: {', '.join(sorted(OLLAMA_MODELS))}. "
        f"OpenAI models: {', '.join(sorted(OPENAI_MODELS))}",
    )
    args = parser.parse_args()

    cleanup_files = []

    try:
        image_paths, cleanup_files = prepare_images(args.input_path)
        data = extract_from_images(image_paths, output_format=args.output_format, model=args.model)

        print(f"\n{'=' * 70}")
        print("EXTRACTED DATA")
        print(f"{'=' * 70}")
        json_output = json.dumps(data, indent=2, ensure_ascii=False)
        print(json_output)

        if args.output:
            output_file = args.output
        else:
            base_name = Path(args.input_path).stem
            output_file = f"extracted_{base_name}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"\nResults saved to: {output_file}")

        # Summary
        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        name_key = "name" if "name" in data else "name"
        print(f"Product: {data.get('name', data.get('name', 'N/A'))}")
        print(f"Latin: {data.get('latin_name', data.get('lateinischer_name', 'N/A'))}")
        print(f"Volume: {data.get('volume', data.get('volumen', 'N/A'))}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        for f in cleanup_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass


if __name__ == "__main__":
    main()
