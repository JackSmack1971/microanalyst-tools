import React from 'react';
import SearchBar from './SearchBar';
import MetricCard from './MetricCard';
import PriceChart from './PriceChart';
import Skeleton from './Skeleton';
import { AlertTriangle } from 'lucide-react';

const Dashboard = ({ data, loading, error, onSearch }) => {
    return (
        <div className="min-h-screen bg-slate-900 text-slate-50 p-6 font-sans">
            <header className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-cyan-500 rounded-full flex items-center justify-center font-bold text-slate-900">M</div>
                    <h1 className="text-xl font-bold tracking-wider">MICROANALYST</h1>
                </div>
                <SearchBar onSearch={onSearch} loading={loading} />
            </header>

            {loading && <Skeleton />}

            {error && (
                <div className="bg-rose-900/20 border border-rose-500/50 p-4 rounded-lg flex items-center gap-3 text-rose-200 mb-8">
                    <AlertTriangle className="h-5 w-5" />
                    <span>{error}</span>
                </div>
            )}

            {!loading && !error && data && (
                <div className="space-y-6">
                    {/* Hero Section */}
                    <div className="flex flex-col md:flex-row justify-between items-end border-b border-slate-800 pb-6">
                        <div>
                            <h2 className="text-4xl font-bold font-mono tracking-tight">{data.token_symbol_api.toUpperCase()}</h2>
                            <div className="text-slate-400 text-sm mt-1">{data.cg_data.name} • Rank #{data.cg_data.market_cap_rank}</div>
                        </div>
                        <div className="text-right mt-4 md:mt-0">
                            <div className="text-5xl font-mono font-bold text-slate-100">
                                ${data.cg_data.market_data.current_price.usd.toLocaleString()}
                            </div>
                            {/* 24h Change would go here if available in top level data, for now we skip or calculate if we had history */}
                        </div>
                    </div>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <MetricCard
                            title="Volatility (CV)"
                            value={data.volatility_metrics.cv?.toFixed(4)}
                            signal={data.volatility_metrics.cv > 0.1 ? 'WARN' : 'OK'}
                            subtext="30-Day Coefficient of Variation"
                        />
                        <MetricCard
                            title="Spread"
                            value={`${data.liquidity_metrics.spread_pct?.toFixed(2)}%`}
                            signal={data.liquidity_metrics.spread_pct > 0.5 ? 'WARN' : 'OK'}
                            subtext="Bid-Ask Spread"
                        />
                        <MetricCard
                            title="Volume Delta"
                            value={`${data.vol_delta?.toFixed(1)}%`}
                            signal={data.vol_delta > 20 ? 'WARN' : 'OK'}
                            subtext="CEX vs Aggregator Divergence"
                        />
                        <MetricCard
                            title="Imbalance"
                            value={data.liquidity_metrics.imbalance?.toFixed(2)}
                            signal={(data.liquidity_metrics.imbalance < 0.5 || data.liquidity_metrics.imbalance > 2.0) ? 'WARN' : 'OK'}
                            subtext="Bid/Ask Ratio"
                        />
                    </div>

                    {/* Charts */}
                    <PriceChart data={data.prices} symbol={data.token_symbol_api} />
                </div>
            )}

            {!loading && !error && !data && (
                <div className="text-center text-slate-500 mt-20">
                    <p>Enter a token symbol to begin analysis.</p>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
