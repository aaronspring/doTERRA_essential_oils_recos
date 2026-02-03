from pydantic import BaseModel, Field


class EssentialOil(BaseModel):
    """
    Pydantic model for essential oil product information.
    Based on doTERRA product information page structure.
    """

    name: str = Field(
        description="The common name of the essential oil product (e.g., 'Wild Orange')"
    )
    latin_name: str = Field(
        description="The botanical Latin name of the plant (e.g., 'Citrus sinensis')"
    )
    application: list[str] = Field(
        description="Application methods with codes: A (Aromatic), T (Topical), I (Internal), N (Neat/Dilution not required)"
    )
    plant_part: list[str] = Field(
        description="Parts of the plant used to extract the oil (e.g., 'Peel', 'Leaf', 'Flower')"
    )
    extraction_method: str = Field(
        description="The method used to extract the essential oil (e.g., 'Cold pressed', 'Steam distillation')"
    )
    aroma_description: list[str] = Field(
        description="Descriptive terms for the oil's scent profile (e.g., 'Sweet', 'Fresh', 'Citrus')"
    )
    main_chemical_constituents: list[str] = Field(
        description="Primary chemical compounds present in the oil (e.g., 'Limonene', 'Linalool')"
    )
    primary_benefits: list[str] = Field(
        description="Key health and wellness benefits supported by the essential oil"
    )
    product_description: str = Field(
        description="Comprehensive overview of the product, including sourcing, properties, and general uses"
    )
    usage_instructions: list[str] = Field(
        description="Specific ways to use the oil in daily routines"
    )
    uses: list[str] = Field(
        description="Practical applications and use cases for the essential oil"
    )
    directions_for_use: list[str] = Field(
        description="Specific instructions for aromatic, internal, and topical application methods"
    )
    cautions: list[str] = Field(
        description="Safety warnings, contraindications, and precautions for use"
    )


# Example instance populated from the Wild Orange product information
wild_orange = EssentialOil(
    name="Wild Orange",
    latin_name="Citrus sinensis",
    application=["A", "T", "I", "N"],
    plant_part=["Peel"],
    extraction_method="Cold pressed",
    aroma_description=["Sweet", "Fresh", "Citrus"],
    main_chemical_constituents=["Limonene"],
    primary_benefits=[
        "Supports healthy inflammatory response when used internally",
        "Creates an uplifting environment",
    ],
    product_description="Cold pressed from the peel, Wild Orange is one of dōTERRA's top selling essential oils due to its energizing aroma and multiple health benefits. High in limonene, Wild Orange may support a healthy inflammatory response when used internally. It can be used as a daily surface cleaner throughout the home. Diffusing Wild Orange will energize and uplift the atmosphere while freshening the air. Wild Orange enhances any essential oil blend with a fresh, sweet, refreshing aroma.",
    usage_instructions=[
        "Mix with water in a spray bottle and spritz on surfaces for a cleansing boost",
        "Add a drop to your water every day for a burst of flavor and to promote overall health",
        "Diffuse for an uplifting aroma and to freshen the air",
        "Place one to two drops in palm of hand, rub hands together, cup over mouth and nose, and inhale deeply for an energizing boost",
    ],
    uses=[
        "Daily surface cleaner throughout the home",
        "Enhances any essential oil blend",
        "Energizes and uplifts the atmosphere",
        "Freshens the air",
    ],
    directions_for_use=[
        "Aromatic use: Use three to four drops in the diffuser of choice",
        "Internal use: Dilute one drop in 4 fluid ounces of liquid",
        "Topical use: Apply one to two drops to desired area. Dilute with a carrier oil to minimize any skin sensitivity",
    ],
    cautions=[
        "Possible skin sensitivity",
        "Keep out of reach of children",
        "If you are pregnant, nursing, or under a doctor's care, consult your physician",
        "Avoid contact with eyes, inner ears, and sensitive areas",
        "Avoid sunlight and UV rays for at least 12 hours after applying product",
    ],
)


if __name__ == "__main__":
    # Print the schema
    print(EssentialOil.model_json_schema())
    print("\n" + "=" * 80 + "\n")
    # Print the example instance
    print(wild_orange.model_dump_json(indent=2))
