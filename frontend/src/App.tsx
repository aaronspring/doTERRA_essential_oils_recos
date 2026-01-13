
import React, { useEffect, useState } from 'react';
import { api } from './api';
import type { SearchResult } from './types';
import { OilCard } from './components/OilCard';
import { Search, Droplets, X } from 'lucide-react';

function App() {
  const [items, setItems] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(true);

  // Store full objects for liked and disliked items
  const [likedItems, setLikedItems] = useState<SearchResult[]>([]);
  const [dislikedItems, setDislikedItems] = useState<SearchResult[]>([]);

  const [searchQuery, setSearchQuery] = useState('');
  const [mode, setMode] = useState<'discovery' | 'search'>('discovery');
  const [error, setError] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    loadInitialDiscovery();
  }, []);

  const loadInitialDiscovery = async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await api.discover();
      setItems(results);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load oils');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setMode('search');
    setLoading(true);
    setError(null);
    try {
      const results = await api.search(searchQuery);
      setItems(results);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const clearAllFeedback = () => {
    setLikedItems([]);
    setDislikedItems([]);
    loadInitialDiscovery();
  };

  const handleLike = async (item: SearchResult) => {
    // If already liked, remove it
    if (likedItems.find(i => i.id === item.id)) {
      handleRemoveLike(item.id);
      return;
    }

    const newLiked = [...likedItems, item];
    setLikedItems(newLiked);

    // Remove from Disliked if present
    const newDisliked = dislikedItems.filter(i => i.id !== item.id);
    setDislikedItems(newDisliked);

    updateRecommendations(newLiked.map(i => i.id), newDisliked.map(i => i.id));
  };

  const handleRemoveLike = (id: number) => {
    const newLiked = likedItems.filter(i => i.id !== id);
    setLikedItems(newLiked);

    if (newLiked.length === 0 && dislikedItems.length === 0) {
      loadInitialDiscovery();
    } else {
      updateRecommendations(newLiked.map(i => i.id), dislikedItems.map(i => i.id));
    }
  };

  const handleDislike = async (item: SearchResult) => {
    // If already disliked, remove it (toggle)
    if (dislikedItems.find(i => i.id === item.id)) {
      handleRemoveDislike(item.id);
      return;
    }

    const newDisliked = [...dislikedItems, item];
    setDislikedItems(newDisliked);

    // Remove from liked if present
    const newLiked = likedItems.filter(i => i.id !== item.id);
    setLikedItems(newLiked);

    updateRecommendations(newLiked.map(i => i.id), newDisliked.map(i => i.id));
  };

  const handleRemoveDislike = (id: number) => {
    const newDisliked = dislikedItems.filter(i => i.id !== id);
    setDislikedItems(newDisliked);

    if (likedItems.length === 0 && newDisliked.length === 0) {
      loadInitialDiscovery();
    } else {
      updateRecommendations(likedItems.map(i => i.id), newDisliked.map(i => i.id));
    }
  };

  const updateRecommendations = async (positiveIds: number[], negativeIds: number[]) => {
    setLoading(true);
    try {
      // Recommendation requires at least one positive item. 
      // If we have no positive items (even if we have negative ones), we fall back to discovery.
      if (positiveIds.length === 0) {
        const results = await api.discover();
        setItems(results);
      } else {
        const results = await api.recommend(positiveIds, negativeIds);
        setItems(results);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Recommendation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
          <div
            className="flex items-center gap-2 cursor-pointer group"
            onClick={() => { setMode('discovery'); clearAllFeedback(); }}
          >
            <div className="bg-gradient-to-br from-rose-500 to-purple-600 p-2 rounded-xl text-white shadow-lg group-hover:shadow-rose-500/30 transition-shadow">
              <Droplets size={20} />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">
              AromaDiscover
            </h1>
          </div>

          <form onSubmit={handleSearch} className="relative w-full md:w-96 group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-rose-500 transition-colors" size={18} />
            <input
              type="text"
              placeholder="Search for 'sleep', 'energy'..."
              className="w-full pl-10 pr-4 py-2.5 rounded-full bg-slate-100 border-none focus:ring-2 focus:ring-rose-500/20 focus:bg-white transition-all outline-none text-sm placeholder:text-slate-400 font-medium"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-12">

        {/* Top Row: Feedback Split (Liked Left, Disliked Right) */}
        {(likedItems.length > 0 || dislikedItems.length > 0) && (
          <section className="animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                Context & Feedback
              </h2>
              <button
                onClick={clearAllFeedback}
                className="text-xs text-slate-400 hover:text-rose-500 font-medium transition-colors"
              >
                Clear All
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left: Positive Feedback */}
              <div className="bg-white/50 rounded-2xl p-4 border border-rose-100/50 relative">
                <div className="absolute top-0 left-0 -translate-y-1/2 translate-x-4 bg-white px-2 py-0.5 rounded-full border border-rose-100 text-[10px] font-bold text-rose-500 uppercase tracking-wide shadow-sm flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Liked ({likedItems.length})
                </div>

                {likedItems.length === 0 ? (
                  <div className="h-24 flex items-center justify-center text-slate-300 text-xs italic border-2 border-dashed border-slate-200 rounded-xl">
                    Add items you like here
                  </div>
                ) : (
                  <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x">
                    {likedItems.map((item) => (
                      <div key={item.id} className="relative flex-shrink-0 w-20 snap-start group">
                        <div className="aspect-[3/4] rounded-lg overflow-hidden border border-rose-100 shadow-sm bg-white relative">
                          <img
                            src={item.payload.product_image_url || '/placeholder_oil.png'}
                            alt={item.payload.product_name}
                            className="w-full h-full object-cover p-1"
                          />
                        </div>
                        <div className="absolute -top-1.5 -right-1.5">
                          <button
                            onClick={() => handleRemoveLike(item.id)}
                            className="bg-white border border-slate-200 rounded-full p-0.5 shadow-sm text-slate-400 hover:text-red-500 transition-colors"
                          >
                            <X size={10} />
                          </button>
                        </div>
                        <p className="mt-1 text-[10px] font-medium text-slate-600 truncate text-center leading-tight">
                          {item.payload.product_name}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right: Negative Feedback */}
              <div className="bg-white/50 rounded-2xl p-4 border border-slate-200/50 relative">
                <div className="absolute top-0 left-0 -translate-y-1/2 translate-x-4 bg-white px-2 py-0.5 rounded-full border border-slate-200 text-[10px] font-bold text-slate-500 uppercase tracking-wide shadow-sm flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Disliked ({dislikedItems.length})
                </div>

                {dislikedItems.length === 0 ? (
                  <div className="h-24 flex items-center justify-center text-slate-300 text-xs italic border-2 border-dashed border-slate-200 rounded-xl">
                    Add items to avoid here
                  </div>
                ) : (
                  <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x">
                    {dislikedItems.map((item) => (
                      <div key={item.id} className="relative flex-shrink-0 w-20 snap-start group">
                        <div className="aspect-[3/4] rounded-lg overflow-hidden border border-slate-200 shadow-sm bg-white relative opacity-75 grayscale-[0.5]">
                          <img
                            src={item.payload.product_image_url || '/placeholder_oil.png'}
                            alt={item.payload.product_name}
                            className="w-full h-full object-cover p-1"
                          />
                        </div>
                        <div className="absolute -top-1.5 -right-1.5">
                          <button
                            onClick={() => handleRemoveDislike(item.id)}
                            className="bg-white border border-slate-200 rounded-full p-0.5 shadow-sm text-slate-400 hover:text-slate-600 transition-colors"
                          >
                            <X size={10} />
                          </button>
                        </div>
                        <p className="mt-1 text-[10px] font-medium text-slate-600 truncate text-center leading-tight">
                          {item.payload.product_name}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Bottom Area: Recommendations */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              {(likedItems.length > 0 || dislikedItems.length > 0) ? 'Recommended for You' : 'Discover'}
            </h2>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="bg-slate-100 rounded-2xl h-80 animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12 bg-red-50 rounded-2xl border border-red-100">
              <p className="text-red-500 mb-4">{error}</p>
              <button
                onClick={() => updateRecommendations(likedItems.map(i => i.id), dislikedItems.map(i => i.id))}
                className="bg-white text-red-500 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 transition font-medium text-sm"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
              {items.map((item) => (
                <OilCard
                  key={item.id}
                  item={item}
                  onLike={() => handleLike(item)}
                  onDislike={() => handleDislike(item)}
                  isLiked={likedItems.some(i => i.id === item.id)}
                  isDisliked={dislikedItems.some(i => i.id === item.id)}
                />
              ))}
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="text-center py-20 text-slate-400">
              <p>No oils found. Try searching for something else.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
