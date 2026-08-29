import React from 'react';

export const LoadingSkeleton: React.FC<{ className?: string }> = ({ className = 'h-4 w-full' }) => {
  return <div className={`animate-pulse bg-slate-200 rounded ${className}`} />;
};

export const KPISkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 border-l-4 border-slate-300 p-4 shadow-sm animate-pulse">
      <div className="h-3 w-24 bg-slate-200 rounded mb-2" />
      <div className="h-7 w-16 bg-slate-300 rounded mb-2" />
      <div className="h-3 w-32 bg-slate-100 rounded" />
    </div>
  );
};
