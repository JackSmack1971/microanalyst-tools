import React from 'react';

const Skeleton = () => {
    return (
        <div className="animate-pulse space-y-4">
            <div className="h-8 bg-slate-700 rounded w-1/4"></div>
            <div className="h-64 bg-slate-700 rounded"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="h-24 bg-slate-700 rounded"></div>
                <div className="h-24 bg-slate-700 rounded"></div>
                <div className="h-24 bg-slate-700 rounded"></div>
                <div className="h-24 bg-slate-700 rounded"></div>
            </div>
        </div>
    );
};

export default Skeleton;
