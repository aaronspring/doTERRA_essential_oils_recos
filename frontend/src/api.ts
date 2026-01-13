import axios from 'axios';
import type { SearchResult } from './types';

const API_URL = 'http://localhost:8000';

export const api = {
    search: async (query: string): Promise<SearchResult[]> => {
        const response = await axios.post(`${API_URL}/search`, { query, limit: 30 });
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
