import React, { useState } from 'react';
import { AlertTriangle, ChevronRight, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DisclaimerBanner: React.FC = () => {
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200/80 text-amber-900 shrink-0">
      <div className="max-w-7xl mx-auto px-4 py-1.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 min-w-0">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <p className="text-[11px] leading-tight">
            <span className="font-bold text-amber-950 uppercase tracking-wide mr-1.5">
              ⚠ Preliminary Decision-Support System
            </span>
            <span className="text-amber-800">
              Not an official relocation authorization or safe-site certification.
              All outputs require geotechnical and administrative review.
            </span>
            <Link
              to="/methodology"
              className="ml-2 inline-flex items-center gap-0.5 text-amber-700 hover:text-amber-950 font-semibold underline underline-offset-2 transition-colors"
            >
              View limitations
              <ChevronRight className="w-3 h-3" />
            </Link>
          </p>
        </div>

        <button
          onClick={() => setIsDismissed(true)}
          className="text-amber-600 hover:text-amber-950 p-0.5 rounded hover:bg-amber-100 shrink-0 transition-colors"
          title="Dismiss banner (limitations remain accessible via Methodology page)"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
