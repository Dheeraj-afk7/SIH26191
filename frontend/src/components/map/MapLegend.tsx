import React from 'react';
import { PRIORITY_TIERS } from '../../config/constants';

interface MapLegendProps {
  showRedZones: boolean;
  showCandidateAreas: boolean;
}

export const MapLegend: React.FC<MapLegendProps> = ({
  showRedZones,
  showCandidateAreas,
}) => {
  return (
    <div className="bg-white/95 backdrop-blur-sm p-3 rounded-lg border border-slate-200 shadow-md text-xs space-y-2.5 max-w-[220px]">
      <p className="font-bold text-slate-900 uppercase tracking-wider text-[10px]">
        Map Legend
      </p>

      {/* Priority Tiers */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-semibold text-slate-500 uppercase">Habitation Priority</p>
        {Object.values(PRIORITY_TIERS).map((tier) => (
          <div key={tier.key} className="flex items-center gap-2">
            <span
              className="rounded-full shrink-0 border border-white shadow-sm"
              style={{
                backgroundColor: tier.mapColor,
                width: `${tier.mapSize * 1.5}px`,
                height: `${tier.mapSize * 1.5}px`,
              }}
            />
            <span className="text-[11px] text-slate-700 leading-tight">
              {tier.shortLabel}
            </span>
          </div>
        ))}
      </div>

      {/* Hazard Red Zones */}
      {showRedZones && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Hazard Context</p>
          <div className="flex items-center gap-2">
            <span className="w-4 h-3 rounded-sm bg-red-500/30 border border-red-600 shrink-0" />
            <span className="text-[11px] text-slate-700 leading-tight">
              Candidate Red Zone (289 zones)
            </span>
          </div>
        </div>
      )}

      {/* Candidate Areas */}
      {showCandidateAreas && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Terrain Screening</p>
          <div className="flex items-center gap-2">
            <span className="w-4 h-3 rounded-sm bg-amber-500/20 border border-amber-600 border-dashed shrink-0" />
            <span className="text-[11px] text-slate-700 leading-tight">
              Candidate Area Context (Screened)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
