import axios from 'axios';
import type { SearchResult } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = {
    search: async (
        query: string,
        usePerplexity: boolean = false,
        likedOils: string[] = [],
        dislikedOils: string[] = [],
        searchType: 'full' | 'aroma' = 'full'
    ): Promise<SearchResult[]> => {
        const endpoint = usePerplexity ? '/search/perplexity' : '/search';
        const payload = {
            query,
            limit: 30,
            liked_oils: likedOils,
            disliked_oils: dislikedOils,
            search_type: searchType
        };
        const response = await axios.post(`${API_URL}${endpoint}`, payload, {
            timeout: 45000  // 45s timeout for Perplexity calls
        });
        return response.data;
    },
    recommend: async (positive: number[], negative: number[] = []): Promise<SearchResult[]> => {
        const response = await axios.post(`${API_URL}/recommend`, {
            positive,
            negative,
            limit: 30
        });
        return response.data;
    },
    discover: async (): Promise<SearchResult[]> => {
        // Initially fetch random or popular items
        const response = await axios.get(`${API_URL}/random?limit=30`);
        return response.data;
    }
};
