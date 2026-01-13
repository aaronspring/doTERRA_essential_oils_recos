import type { SearchResult } from '../types';
import { motion } from 'framer-motion';
import { Heart, ThumbsDown, ExternalLink } from 'lucide-react';

interface OilCardProps {
    item: SearchResult;
    onLike: (item: SearchResult) => void;
    onDislike: (item: SearchResult) => void;
    isLiked?: boolean;
    isDisliked?: boolean;
}

export function OilCard({ item, onLike, onDislike, isLiked, isDisliked }: OilCardProps) {
    return (
        <div className="group relative bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
            {/* Buy Link Top Left */}
            <div className="absolute top-3 left-3 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                {item.payload.product_url && (
                    <a
                        href={item.payload.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-full text-[10px] font-bold text-slate-600 hover:text-rose-500 hover:bg-white transition-all shadow-sm"
                    >
                        <span>Buy</span>
                        <ExternalLink size={10} />
                    </a>
                )}
            </div>

            {/* Image Area */}
            <div className="aspect-square relative overflow-hidden bg-slate-50 p-6 flex items-center justify-center">
                <motion.img
                    src={item.payload.product_image_url || '/placeholder_oil.png'}
                    alt={item.payload.product_name}
                    className="w-full h-full object-contain mix-blend-multiply filter drop-shadow-sm"
                    whileHover={{ scale: 1.05 }}
                    transition={{ duration: 0.3 }}
                />

                {/* Overlay actions - Removed non-functional placeholders for cleanup */}
            </div>

            {/* Content Area */}
            <div className="p-4">
                <div className="mb-3">
                    <h3 className="font-bold text-slate-800 text-lg leading-tight mb-1 truncate" title={item.payload.product_name}>
                        {item.payload.product_name}
                    </h3>
                    <p className="text-xs text-slate-500 italic font-medium truncate">{item.payload.product_sub_name}</p>
                </div>

                <p className="text-sm text-slate-600 line-clamp-2 mb-4 h-10">
                    {item.payload.product_description || 'No description available.'}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                    <button
                        onClick={() => onDislike(item)}
                        className={`p-2 rounded-full transition-colors ${isDisliked
                            ? 'bg-slate-800 text-white shadow-lg'
                            : 'bg-slate-100 text-slate-400 hover:bg-slate-200 hover:text-slate-600'
                            }`}
                        title="Less like this"
                    >
                        <ThumbsDown size={18} fill={isDisliked ? "currentColor" : "none"} />
                    </button>

                    <button
                        onClick={() => onLike(item)}
                        className={`p-2 rounded-full transition-colors ${isLiked
                            ? 'bg-rose-500 text-white shadow-lg'
                            : 'bg-slate-100 text-slate-400 hover:bg-rose-50 hover:text-rose-600'
                            }`}
                        title="More like this"
                    >
                        <Heart size={18} fill={isLiked ? "currentColor" : "none"} />
                    </button>
                </div>
            </div>
        </div>
    );
};
