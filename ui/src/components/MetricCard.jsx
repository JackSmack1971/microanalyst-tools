import React from 'react';
import clsx from 'clsx';

const MetricCard = ({ title, value, signal, subtext }) => {
    const isPositive = signal === 'OK';
    const isNegative = signal === 'HIGH';
    const isWarning = signal === 'WARN';

    return (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 shadow-lg">
            <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-1">{title}</h3>
            <div className={clsx(
                "text-2xl font-mono font-bold",
                isPositive && "text-emerald-400",
                isNegative && "text-rose-400",
                isWarning && "text-yellow-400",
                !isPositive && !isNegative && !isWarning && "text-slate-200"
            )}>
                {value}
            </div>
            {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
        </div>
    );
};

export default MetricCard;
