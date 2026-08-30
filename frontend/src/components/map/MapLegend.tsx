import React from 'react';
import { PRIORITY_TIERS } from '../../config/constants';
import { InfoTooltip } from '../shared/InfoTooltip';

interface MapLegendProps {
  showRedZones: boolean;
  showCandidateAreas: boolean;
  showInfrastructure?: boolean;
  showDisasters?: boolean;
  showRoads?: boolean;
}

export const MapLegend: React.FC<MapLegendProps> = ({
  showRedZones,
  showCandidateAreas,
  showInfrastructure = true,
  showDisasters = true,
  showRoads = true,
}) => {
  return (
    <div className="bg-white/95 backdrop-blur-sm p-3 rounded-lg border border-slate-200 shadow-md text-xs space-y-2.5 max-w-[250px] max-h-[480px] overflow-y-auto">
      <div className="flex items-center justify-between border-b border-slate-100 pb-1">
        <p className="font-bold text-slate-900 uppercase tracking-wider text-[10px]">
          GIS Map Legend
        </p>
        <InfoTooltip
          title="Map Symbol Key"
          content="Symbols and color ramps representing habitations, hazard boundaries, candidate relocation terrain, and contextual lifelines."
          side="top"
        />
      </div>

      {/* 1. Core Decision: Priority Tiers */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Habitation Priority (653)</p>
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
                  width: `${tier.mapSize * 1.4}px`,
                  height: `${tier.mapSize * 1.4}px`,
                }}
              />
              <span className="text-[11px] text-slate-700 leading-tight">
                {tier.shortLabel}
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {tier.key === 'Tier1_AttentionPriority' ? '12' : tier.key === 'Tier2_ElevatedAttention' ? '69' : tier.key === 'Tier3_Monitoring' ? '204' : '368'}
            </span>
          </div>
        ))}
      </div>

      {/* 2. Core Decision: Hazard Red Zones */}
      {showRedZones && (
        <div className="pt-1.5 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Hazard Red Zones (289)</p>
          <div className="flex items-center gap-2">
            <span className="w-4 h-2.5 rounded-sm bg-red-500/30 border border-red-600 shrink-0" />
            <span className="text-[11px] text-slate-700 leading-tight">
              Candidate Red Zone
            </span>
          </div>
        </div>
      )}

      {/* 3. Core Decision: Candidate Areas */}
      {showCandidateAreas && (
        <div className="pt-1.5 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Candidate Terrain (2,998)</p>
          <div className="flex items-center gap-2">
            <span className="w-4 h-2.5 rounded-sm bg-amber-500/20 border border-amber-600 border-dashed shrink-0" />
            <span className="text-[11px] text-slate-700 leading-tight">
              Screened Terrain Cluster
            </span>
          </div>
        </div>
      )}

      {/* 4. Contextual: Critical Infrastructure */}
      {showInfrastructure && (
        <div className="pt-1.5 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Facilities (291 Contextual)</p>
          <div className="space-y-1 text-[11px] text-slate-700">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600 border border-white shrink-0" />
              <span>Hospital / CHC / PHC (42)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-600 border border-white shrink-0" />
              <span>Health SubCentre / Clinic (145)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 border border-white shrink-0" />
              <span>Education Facility (70)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-900 border border-white shrink-0" />
              <span>Police / Fire Station (4)</span>
            </div>
          </div>
        </div>
      )}

      {/* 5. Contextual: Historical Disasters */}
      {showDisasters && (
        <div className="pt-1.5 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Historical Disasters (22)</p>
          <div className="space-y-1 text-[11px] text-slate-700">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-600 border border-white shrink-0" />
              <span>Historical Landslide (14)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-600 border border-white shrink-0" />
              <span>Flash Flood / Cloudburst (8)</span>
            </div>
          </div>
        </div>
      )}

      {/* 6. Contextual: Arterial Road Network */}
      {showRoads && (
        <div className="pt-1.5 border-t border-slate-100 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase">Arterial Roads (Phase 2)</p>
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-blue-600 shrink-0" />
            <span className="text-[11px] text-slate-700 leading-tight">
              NH-107 / NH-07 Corridors
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
