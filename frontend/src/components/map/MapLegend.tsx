import React from 'react';
import { PRIORITY_TIERS } from '../../config/constants';
import { InfoTooltip } from '../shared/InfoTooltip';

interface MapLegendProps {
  showRedZones: boolean;
  showCandidateAreas: boolean;
}

export const MapLegend: React.FC<MapLegendProps> = ({
  showRedZones,
  showCandidateAreas,
}) => {
  return (
    <div className="bg-white/95 backdrop-blur-sm p-3 rounded-lg border border-slate-200 shadow-md text-xs space-y-2.5 max-w-[240px]">
      <div className="flex items-center justify-between">
        <p className="font-bold text-slate-900 uppercase tracking-wider text-[10px]">
          Map Legend
        </p>
        <InfoTooltip
          title="Map Symbol Key"
          content="Symbols and color ramps representing habitations, hazard boundaries, and candidate relocation terrain."
          side="top"
        />
      </div>

      {/* Priority Tiers */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Habitation Priority</p>
          <InfoTooltip
            title="Habitation Priority Points"
            content="653 habitation centroid markers color-coded and sized according to deterministic screening priority."
            side="top"
          />
        </div>
        {Object.values(PRIORITY_TIERS).map((tier) => (
          <div key={tier.key} className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-2">
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
            <InfoTooltip
              title={tier.label}
              content={tier.description}
              formula={tier.key === 'Tier1_AttentionPriority' ? 'Dist ≤ 500m & MH Class ≥ 2' : tier.key === 'Tier2_ElevatedAttention' ? 'Dist ≤ 2000m' : tier.key === 'Tier3_Monitoring' ? 'Dist ≤ 5000m' : 'Dist > 5000m'}
              side="right"
              size="xs"
            />
          </div>
        ))}
      </div>

      {/* Hazard Red Zones */}
      {showRedZones && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Hazard Context</p>
            <InfoTooltip
              title="Red Zone Polygons"
              content="289 vector polygons representing moderate-to-higher multi-hazard screening extent from 30m DEM slope + flood proxies."
              side="top"
            />
          </div>
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-2">
              <span className="w-4 h-3 rounded-sm bg-red-500/30 border border-red-600 shrink-0" />
              <span className="text-[11px] text-slate-700 leading-tight">
                Candidate Red Zone (289)
              </span>
            </div>
            <InfoTooltip
              title="Candidate Red Zones"
              content="Derived from terrain susceptibility and flood wetness index. Not official certified government evacuation zones."
              side="right"
            />
          </div>
        </div>
      )}

      {/* Candidate Areas */}
      {showCandidateAreas && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Terrain Screening</p>
            <InfoTooltip
              title="Candidate Terrain Polygons"
              content="Preliminary terrain polygons with low-to-moderate slopes located outside red zones."
              side="top"
            />
          </div>
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-2">
              <span className="w-4 h-3 rounded-sm bg-amber-500/20 border border-amber-600 border-dashed shrink-0" />
              <span className="text-[11px] text-slate-700 leading-tight">
                Candidate Area Context
              </span>
            </div>
            <InfoTooltip
              title="Candidate Relocation Context"
              content="Screened low-slope terrain. Requires mandatory field geotechnical assessment and administrative review."
              side="right"
            />
          </div>
        </div>
      )}
    </div>
  );
};
