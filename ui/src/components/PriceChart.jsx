import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PriceChart = ({ data, symbol }) => {
    if (!data || data.length === 0) return null;

    const chartData = data.map((price, index) => ({
        date: index, // Simplified for now, ideally pass dates
        value: price
    }));

    return (
        <div className="w-full h-64 bg-slate-800 rounded-lg p-4 border border-slate-700 shadow-lg">
            <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">{symbol} Price History (30D)</h3>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={['auto', 'auto']} hide />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                        itemStyle={{ color: '#06b6d4' }}
                        formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                        labelFormatter={() => ''}
                    />
                    <Area type="monotone" dataKey="value" stroke="#06b6d4" fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default PriceChart;
