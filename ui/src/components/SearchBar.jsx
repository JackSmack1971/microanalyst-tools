import React, { useState } from 'react';
import { Search } from 'lucide-react';

const SearchBar = ({ onSearch, loading }) => {
    const [query, setQuery] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative w-full max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-400" />
            </div>
            <input
                type="text"
                className="block w-full pl-10 pr-3 py-2 border border-slate-700 rounded-md leading-5 bg-slate-800 text-slate-100 placeholder-slate-400 focus:outline-none focus:bg-slate-900 focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
                placeholder="Search Token (e.g. BTC)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
            />
        </form>
    );
};

export default SearchBar;
