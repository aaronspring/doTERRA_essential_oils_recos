export interface ProductPayload {
    product_name: string;
    product_sub_name?: string;
    product_image_url?: string;
    product_description?: string;
    brand_lifestyle_title?: string;
    brand_lifestyle_description?: string;
    shop_url?: string;
}

export interface SearchResult {
    id: number;
    score: number;
    payload: ProductPayload;
    source?: 'embedding' | 'perplexity';
}
