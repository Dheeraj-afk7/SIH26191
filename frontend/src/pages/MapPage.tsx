import React from 'react';
import { Map as MapIcon, Building2, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { GisMap } from '../components/map/GisMap';
import { MANDATORY_DISCLAIMERS } from '../config/constants';
import { InfoTooltip } from '../components/shared/InfoTooltip';

export const MapPage: React.FC = () => {
  return (
    <div className="space-y-4">
      {/* Page Header with Demo Flow Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <MapIcon className="w-5 h-5 text-blue-700" />
              Interactive GIS Decision-Support Map
            </h2>
            <InfoTooltip
              title="Spatial Map Overview"
              content="Dynamic multi-layer GIS viewport rendering 289 candidate hazard red zones, 653 habitations with tier styling, and candidate terrain extents."
              side="bottom"
            />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Spatial multi-layer viewer · Rudraprayag District · 289 Candidate Red Zones · 653 Village Points · Candidate Terrain
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Link
            to="/villages"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
          >
            <Building2 className="w-3.5 h-3.5" />
            Open Village Explorer
            <ArrowRight className="w-3 h-3" />
          </Link>
          <InfoTooltip
            title="Village Explorer"
            content="Search, filter, and inspect detailed profiles for all 653 habitations in tabular format."
            side="bottom"
          />
        </div>
      </div>

      {/* Main Interactive Leaflet Map */}
      <GisMap />

      {/* Spatial Data Limitation Notice */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Spatial Layer Methodological Disclaimer
          </h4>
          <InfoTooltip
            title="Spatial Data Caveats"
            content="Highlights spatial scale and precision limits of 30m DEM derivatives, reference centroids, and preliminary vector boundaries."
            side="left"
          />
        </div>
        <ul className="space-y-1.5 text-xs text-slate-600">
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5 shrink-0">•</span>
            <span>
              <strong className="text-slate-800">{MANDATORY_DISCLAIMERS.CENTROID_LIMITATION}</strong>&nbsp;
              Direct centroid distance to red zone boundary is a proxy metric;
              actual habitation perimeters may be closer to hazard terrain.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5 shrink-0">•</span>
            <span>
              <strong className="text-slate-800">Candidate Red Zones:</strong>&nbsp;
              289 vector polygons representing moderate-to-higher multi-hazard screening extent derived
              from 30m DEM derivatives. Requires official geotechnical assessment.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5 shrink-0">•</span>
            <span>
              <strong className="text-slate-800">Candidate Topographically Feasible Areas:</strong>&nbsp;
              Screened terrain polygons loaded dynamically based on current map viewport (BBox spatial indexing).
              NOT certified safe sites.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
};
