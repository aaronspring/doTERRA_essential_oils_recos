#!/usr/bin/env python3
"""
doTERRA EU/de Product Information Page (PIP) PDF URL Generator and Fetcher

This script generates all known doTERRA essential oil PDF URLs for the EU region
and German language, and can optionally verify which URLs are valid.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class DoterraPDFGenerator:
    """Generates and fetches doTERRA EU/de PIP PDF URLs."""

    BASE_URL = "https://media.doterra.com/eu/de/pips"

    # Single oils (typically use pattern: {name}-oil.pdf)
    SINGLE_OILS = [
        "arborvitae",
        "basil",
        "bergamot",
        "birch",
        "black-pepper",
        "black-spruce",
        "blue-tansy",
        "cardamom",
        "cassia",
        "cedarwood",
        "cilantro",
        "cinnamon-bark",
        "citronella",
        "clary-sage",
        "clove",
        "cop",
        "coriander",
        "cypress",
        "douglas-fir",
        "eucalyptus",
        "fennel",
        "frankincense",
        "geranium",
        "ginger",
        "grapefruit",
        "green-mandarin",
        "helichrysum",
        "juniper-berry",
        "lavender",
        "lemon",
        "lemongrass",
        "lime",
        "litsea",
        "manuka",
        "marjoram",
        "melaleuca",
        "melissa",
        "myrrh",
        "neroli",
        "olive",
        "oregano",
        "patchouli",
        "peppermint",
        "petitgrain",
        "pink-pepper",
        "roman-chamomile",
        "rose",
        "rosemary",
        "sandalwood",
        "siberian-fir",
        "spearmint",
        "spikenard",
        "tangerine",
        "thyme",
        "turmeric",
        "vetiver",
        "wild-orange",
        "wintergreen",
        "ylang-ylang",
        # Additional single oils
        "blue-cypress",
        "cade-wood",
        "calamus",
        "cananga",
        "carrot-seed",
        "celery-seed",
        "coffee",
        "dill",
        "elemi",
        "german-chamomile",
        "gold-ribbon",
        "ho-wood",
        "holy-basil",
        "huang-qi",
        "jasmine",
        "kumquat",
        "laurus-nobilis",
        "lemon-balm",
        "lemongrass-massage",
        "magnolia",
        "mandarin",
        "myrtle",
        "neem",
        "neroli-touch",
        "niaouli",
        "palmarosa",
        "palo-santo",
        "ravintsara",
        "rose-otto",
        "rue",
        "sandalwood-hawaiian",
        "savory",
        "tansy",
        "tarragon",
        "tsuga",
        "valerian",
        "white-fir",
        "wild-orange-touch",
        "wintergreen-massage",
        "xanthoxylum",
        "yellow-mandarin",
        "yuzu",
    ]

    # Proprietary blends (typically use pattern: doterra-{name}.pdf)
    PROPRIETARY_BLENDS = [
        "aromatouch",
        "adaptiv",
        "balance",
        "breathe",
        "cheer",
        "citrus-bliss",
        "clarycalm",
        "clearify",
        "ddr-prime",
        "deep-blue",
        "digestzen",
        "doterra-air",
        "doterra-breathe",
        "doterra-on-guard",
        "elevation",
        "forgive",
        "hd-clear",
        "immortelle",
        "in-tune",
        "lavender-peace",
        "motivate",
        "on-guard",
        "passion",
        "past-tense",
        "peace",
        "purify",
        "salon-essentials",
        "serenity",
        "slim-sassy",
        "smart-sassy",
        "terra-armor",
        "terra-shield",
        "whisper",
        "zenGest",
        "zendocrine",
        # Additional blends
        "aromatouch-technique",
        "deep-blue-soothing-blend",
        "digestzen-touch",
        "easy-air",
        "magnolia-touch",
        "neroli-touch",
        "rose-touch",
        "ylang-touch",
        "balance-touch",
        "breathe-touch",
        "cheer-touch",
        "citrus-bliss-touch",
        "doterra-air-touch",
        "doterra-breathe-touch",
        "elevation-touch",
        "forgive-touch",
        "motivate-touch",
        "on-guard-touch",
        "passion-touch",
        "peace-touch",
        "purify-touch",
        "serenity-touch",
        "zenGest-touch",
    ]

    # Touch products (diluted roll-ons, typically use pattern: {name}-touch-oil.pdf)
    TOUCH_PRODUCTS = [
        "aromatouch-touch",
        "balance-touch",
        "breathe-touch",
        "cheer-touch",
        "citrus-bliss-touch",
        "clarycalm-touch",
        "clearify-touch",
        "ddr-prime-touch",
        "deep-blue-touch",
        "digestzen-touch",
        "doterra-air-touch",
        "doterra-breathe-touch",
        "elevation-touch",
        "forgive-touch",
        "frankincense-touch",
        "geranium-touch",
        "hd-clear-touch",
        "helichrysum-touch",
        "immortelle-touch",
        "in-tune-touch",
        "lavender-touch",
        "lavender-peace-touch",
        "lemon-touch",
        "lime-touch",
        "magnolia-touch",
        "melaleuca-touch",
        "motivate-touch",
        "neroli-touch",
        "on-guard-touch",
        "oregano-touch",
        "passion-touch",
        "past-tense-touch",
        "patchouli-touch",
        "peace-touch",
        "peppermint-touch",
        "petitgrain-touch",
        "purify-touch",
        "rose-touch",
        "sandalwood-touch",
        "serenity-touch",
        "slim-sassy-touch",
        "smart-sassy-touch",
        "terra-armor-touch",
        "terra-shield-touch",
        "thyme-touch",
        "vetiver-touch",
        "whisper-touch",
        "wild-orange-touch",
        "ylang-ylang-touch",
        "zenGest-touch",
        "zendocrine-touch",
    ]

    # Kids collection
    KIDS_PRODUCTS = [
        "calmer",
        "rescue",
        "steady",
        "stronger",
        "thinker",
    ]

    # MetaPWR products
    METAPWR_PRODUCTS = [
        "metapwr-advantage",
        "metapwr-amber-oil",
        "metapwr-beauty-cream",
        "metapwr-bundle",
        "metapwr-gum",
        "metapwr-help",
        "metapwr-lifelong-vitality",
        "metapwr-mito2max",
        "metapwr-oil",
        "metapwr-recharge",
        "metapwr-satin-gel",
        "metapwr-softgels",
        "metapwr-trimshake",
    ]

    # Supplements and other products
    SUPPLEMENTS = [
        "alphacrs",
        "bone-nutrient",
        "bone-nutrient-lifelong-vitality",
        "chewable-vitamins",
        "childrens-vitamins",
        "copalyocell",
        "daily-vitality",
        "digestzen-terrazyme",
        "doterra-omega",
        "doterra-on-guard-beadlets",
        "doterra-on-guard-cleansing-toothpaste",
        "doterra-on-guard-floss",
        "doterra-on-guard-mouthwash",
        "doterra-on-guard-plus",
        "doterra-on-guard-protecting-throat-drops",
        "doterra-on-guard-sanitizing-mist",
        "doterra-omega-3",
        "fermented-berries-and-greens",
        "lifelong-vitality-complex",
        "lifelong-vitality-pack",
        "microplex-vmz",
        "mito2max",
        "on-guard-beadlets",
        "on-guard-plus",
        "on-guard-protecting-throat-drops",
        "on-guard-sanitizing-mist",
        "pb-assist",
        "pb-assist-jr",
        "phosso",
        "plex",
        "terrazyme",
        "vegan-microplex",
        "vegan-omega",
        "vegan-vitality",
        "vegan-vitality-pack",
        "vida-de-la-vida",
        "vox-zenGest",
        "vox-zenGest-softgels",
        "xeo-mega",
        "xergo",
    ]

    # Personal care and skin care
    PERSONAL_CARE = [
        "abode",
        "abode-hand-wash",
        "abode-laundry-pods",
        "abode-surface-cleaner",
        "abode-dishwasher-pods",
        "abode-multi-purpose-cleaner",
        "anti-aging-moisturizer",
        "applicator",
        "aromatouch-diffused",
        "aromatouch-hand-technique",
        "aromatouch-technique-kit",
        "body-lotion",
        "body-wash",
        "conditioner",
        "daily-shampoo",
        "deep-blue-rub",
        "deep-blue-stick",
        "deep-blue-spray",
        "deep-blue-polyphenol-complex",
        "dental-floss",
        "deodorant",
        "detoxifying-mask",
        "diffuser-bracelet",
        "diffuser-car-clip",
        "diffuser-key-chain",
        "diffuser-necklace",
        "diffuser-pendant",
        "exfoliating-scrub",
        "eye-cream",
        "face-lotion",
        "facial-cleanser",
        "firming-gel",
        "foot-mask",
        "fractionated-coconut-oil",
        "hair-mask",
        "hand-lotion",
        "hydrating-cream",
        "hydrating-mist",
        "invigorating-scrub",
        "lip-balm",
        "lip-gloss",
        "makeup-brush",
        "mouthwash",
        "on-guard-cleaner-concentrate",
        "on-guard-detergent",
        "on-guard-fabric-softener",
        "on-guard-foaming-hand-wash",
        "on-guard-hand-wash",
        "on-guard-healthy-toothpaste",
        "on-guard-toothpaste",
        "on-guard-wipes",
        "pore-reducing-toner",
        "replenishing-body-butter",
        "salon-essentials-root-to-tip-serum",
        "salon-essentials-shampoo",
        "salon-essentials-conditioner",
        "shampoo",
        "shaving-cream",
        "skin-care-collection",
        "soap-bar",
        "spa-body-butter",
        "spa-hand-lotion",
        "spa-lip-balm",
        "spa-moisturizing-bath-bar",
        "spa-exfoliating-body-scrub",
        "spa-hydrating-body-mist",
        "sun-face-and-body-mineral-sunscreen",
        "sun-face-mineral-sunscreen",
        "sun-mineral-sunscreen-stick",
        "sun-mineral-sunscreen-spray",
        "sun-nourishing-body-mist",
        "sun-recovery-complex",
        "sunscreen-lotion",
        "toothpaste",
        "tightening-serum",
        "treatment-oil",
        "veraage-cleanser",
        "veraage-toner",
        "veraage-moisturizer",
        "veraage-serum",
        "veraage-immortelle",
        "veraage-moisturizer-with-immortelle",
    ]

    # Known working URLs (discovered through research)
    KNOWN_WORKING_URLS = [
        "https://media.doterra.com/eu/de/pips/rose-touch-oil.pdf",
    ]

    def __init__(self, verify_urls: bool = False, max_workers: int = 10):
        """
        Initialize the generator.

        Args:
            verify_urls: If True, will verify each URL by making HTTP requests
            max_workers: Number of concurrent workers for URL verification
        """
        self.verify_urls = verify_urls
        self.max_workers = max_workers
        self.session = requests.Session() if verify_urls else None
        if self.session:
            self.session.headers.update(
                {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

    def _generate_single_oil_urls(self) -> list[str]:
        """Generate URLs for single essential oils."""
        urls = []
        for oil in self.SINGLE_OILS:
            # Try multiple naming patterns
            urls.append(f"{self.BASE_URL}/{oil}-oil.pdf")
            urls.append(f"{self.BASE_URL}/{oil}-essential-oil.pdf")
            urls.append(f"{self.BASE_URL}/{oil.replace('-', '')}-oil.pdf")
        return urls

    def _generate_blend_urls(self) -> list[str]:
        """Generate URLs for proprietary blends."""
        urls = []
        for blend in self.PROPRIETARY_BLENDS:
            # Try multiple naming patterns
            urls.append(f"{self.BASE_URL}/{blend}-oil.pdf")
            urls.append(f"{self.BASE_URL}/doterra-{blend}.pdf")
            urls.append(f"{self.BASE_URL}/doterra-{blend}-oil.pdf")
            urls.append(f"{self.BASE_URL}/{blend}-essential-oil-blend.pdf")
        return urls

    def _generate_touch_urls(self) -> list[str]:
        """Generate URLs for Touch products."""
        urls = []
        for touch in self.TOUCH_PRODUCTS:
            # Try multiple naming patterns
            urls.append(f"{self.BASE_URL}/{touch}-oil.pdf")
            urls.append(f"{self.BASE_URL}/doterra-{touch}-oil.pdf")
            urls.append(f"{self.BASE_URL}/doterra-touch-{touch.replace('-touch', '')}-oil.pdf")
        return urls

    def _generate_kids_urls(self) -> list[str]:
        """Generate URLs for Kids collection."""
        urls = []
        for kid in self.KIDS_PRODUCTS:
            urls.append(f"{self.BASE_URL}/{kid}-oil.pdf")
            urls.append(f"{self.BASE_URL}/doterra-{kid}.pdf")
        return urls

    def _generate_metapwr_urls(self) -> list[str]:
        """Generate URLs for MetaPWR products."""
        urls = []
        for meta in self.METAPWR_PRODUCTS:
            urls.append(f"{self.BASE_URL}/{meta}.pdf")
            urls.append(f"{self.BASE_URL}/{meta}-oil.pdf")
        return urls

    def _generate_supplement_urls(self) -> list[str]:
        """Generate URLs for supplements."""
        urls = []
        for supp in self.SUPPLEMENTS:
            urls.append(f"{self.BASE_URL}/{supp}.pdf")
            urls.append(f"{self.BASE_URL}/{supp}-oil.pdf")
            urls.append(f"{self.BASE_URL}/doterra-{supp}.pdf")
        return urls

    def _generate_personal_care_urls(self) -> list[str]:
        """Generate URLs for personal care products."""
        urls = []
        for care in self.PERSONAL_CARE:
            urls.append(f"{self.BASE_URL}/{care}.pdf")
        return urls

    def generate_all_urls(self) -> list[str]:
        """Generate all possible URLs."""
        all_urls = set()

        # Add known working URLs first
        all_urls.update(self.KNOWN_WORKING_URLS)

        # Generate URLs from all categories
        all_urls.update(self._generate_single_oil_urls())
        all_urls.update(self._generate_blend_urls())
        all_urls.update(self._generate_touch_urls())
        all_urls.update(self._generate_kids_urls())
        all_urls.update(self._generate_metapwr_urls())
        all_urls.update(self._generate_supplement_urls())
        all_urls.update(self._generate_personal_care_urls())

        return sorted(list(all_urls))

    def _verify_single_url(self, url: str) -> str | None:
        """Verify a single URL by making an HTTP HEAD request."""
        if not self.session:
            return url

        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "pdf" in content_type.lower():
                    return url
        except requests.RequestException:
            pass
        return None

    def verify_urls_concurrent(self, urls: list[str]) -> list[str]:
        """Verify URLs concurrently and return only valid ones."""
        if not self.verify_urls or not self.session:
            return urls

        valid_urls = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._verify_single_url, url): url for url in urls}

            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    valid_urls.append(result)
                    print(f"✓ Valid: {result}")

        return sorted(valid_urls)

    def get_all_urls(self, verify: bool | None = None) -> list[str]:
        """
        Get all PDF URLs.

        Args:
            verify: Override the instance verify_urls setting

        Returns:
            List of PDF URLs
        """
        should_verify = verify if verify is not None else self.verify_urls
        urls = self.generate_all_urls()

        if should_verify:
            print(f"Verifying {len(urls)} URLs...")
            urls = self.verify_urls_concurrent(urls)
            print(f"Found {len(urls)} valid URLs")

        return urls

    def save_to_json(self, urls: list[str], filename: str = "doterra_eu_de_pips.json"):
        """Save URLs to a JSON file."""
        data = {
            "region": "eu",
            "language": "de",
            "base_url": self.BASE_URL,
            "total_urls": len(urls),
            "urls": urls,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(urls)} URLs to {filename}")

    def save_to_txt(self, urls: list[str], filename: str = "doterra_eu_de_pips.txt"):
        """Save URLs to a text file, one per line."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))

        print(f"Saved {len(urls)} URLs to {filename}")


def get_all_pdf_urls(verify: bool = False) -> list[str]:
    """
    Convenience function to get all PDF URLs.

    Args:
        verify: If True, will verify each URL by making HTTP requests

    Returns:
        List of PDF URLs
    """
    generator = DoterraPDFGenerator(verify_urls=verify)
    return generator.get_all_urls()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate doTERRA EU/de PIP PDF URLs")
    parser.add_argument(
        "--verify",
        "-v",
        action="store_true",
        help="Verify URLs by making HTTP requests",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "txt", "print"],
        default="print",
        help="Output format",
    )
    parser.add_argument(
        "--filename",
        "-f",
        default=None,
        help="Output filename (default: auto-generated)",
    )

    args = parser.parse_args()

    # Generate URLs
    generator = DoterraPDFGenerator(verify_urls=args.verify)
    urls = generator.get_all_urls()

    # Output results
    if args.output == "print":
        for url in urls:
            print(url)
    elif args.output == "json":
        filename = args.filename or "doterra_eu_de_pips.json"
        generator.save_to_json(urls, filename)
    elif args.output == "txt":
        filename = args.filename or "doterra_eu_de_pips.txt"
        generator.save_to_txt(urls, filename)

    print(f"\nTotal URLs: {len(urls)}")
