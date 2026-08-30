import React from 'react';
import { BookOpenCheck, AlertTriangle, ShieldAlert, RefreshCw, Users, Layers, ShieldCheck } from 'lucide-react';
import { StatusBadge } from '../components/shared/StatusBadge';
import { InfoTooltip } from '../components/shared/InfoTooltip';

export const MethodologyPage: React.FC = () => {
  const dataMatrix = [
    { name: 'Copernicus GLO-30 DEM', source: 'ESA / Copernicus Open Access', status: 'AVAILABLE', role: 'Slope, aspect, hydrology (TWI)', tip: 'Global 30m digital elevation model processed in UTM Zone 44N.' },
    { name: 'Census of India 2011 (PCA)', source: 'Office of the Registrar General & Census Commissioner', status: 'AVAILABLE', role: 'Village population, households, literacy, demographics', tip: 'Primary Census Abstract baseline attributes for 653 habitations.' },
    { name: 'SHRUG v2.2 Spatial Centroids', source: 'Development Data Lab', status: 'AVAILABLE', role: 'Administrative village centroid points', tip: 'Administrative polygon centroids matching Census 2011 village identifiers.' },
    { name: 'ESA WorldCover 10m LULC (Phase 1)', source: 'European Space Agency (ESA WorldCover 2021 v200)', status: 'AVAILABLE', role: 'Ecological & land-cover exclusions (Tree cover, Built-up, Snow/Ice, Water)', tip: 'Categorical 30m grid reprojection; KWLS statutory exclusion pluggable.' },
    { name: 'Routable Road Network (Phase 2)', source: 'OpenStreetMap Contributors', status: 'AVAILABLE', role: 'Mountain impedance & accessibility routing (6,397.3 km)', tip: 'Routable NetworkX Dijkstra graph with empirical mountain speeds in EPSG:32644.' },
    { name: 'Historical Disaster Inventory (Phase 3)', source: 'Peer-Reviewed Published Secondary Literature', status: 'AVAILABLE', role: 'Multi-year disaster history context (22 canonical events, 6,913 fatalities)', tip: 'Literature curated events (1998-2024) with bounded coordinate uncertainty and evidence levels.' },
    { name: 'Critical Infrastructure (Phase 4)', source: 'OpenStreetMap Contributors', status: 'AVAILABLE', role: 'Lifeline proximity & travel time (291 facilities: 187 health, 70 edu, 4 emergency)', tip: 'Deterministic classification with explicit emergency capability semantics.' },
    { name: 'PMAY-G Capacity Standard', source: 'Ministry of Rural Development, GoI (2016)', status: 'AVAILABLE', role: 'Preliminary spatial capacity scenario (25 m²/HH, 40% site efficiency, max 100 ha cap)', tip: 'PMAY-G minimum built floor area standard applied to candidate terrain clusters.' },
  ];

  const innovations = [
    {
      title: 'Dynamic Update & Recomputation Architecture (Phase A)',
      icon: <RefreshCw className="w-4 h-4 text-blue-600" />,
      desc: 'Operator-triggered workflow (POST /api/pipeline/recompute) allowing authorities to recalculate village hazard tiers and candidate area capacity within seconds whenever thresholds or datasets are updated.',
    },
    {
      title: 'Disaster History Integration Readiness (Phase B)',
      icon: <ShieldAlert className="w-4 h-4 text-amber-600" />,
      desc: 'Standardized GeoJSON/JSON incident schema (schema.json) and validation pipeline (validate_disaster_data.py) ready for immediate ingestion of verified USDMA/NDMA disaster records.',
    },
    {
      title: 'Data-Benchmarked Vulnerability Context (Phase C)',
      icon: <Users className="w-4 h-4 text-indigo-600" />,
      desc: 'Four demographic flags benchmarked directly against Rudraprayag Census 2011 upper tertiles (P75): Child Pop (>15.1%), SC Pop (>24.6%), Dependency (>57.9%), and Illiteracy (>34.0%). Provided as context without altering tier assignment.',
    },
    {
      title: 'Defensible Carrying Capacity with Scale Protection (Phase D)',
      icon: <Layers className="w-4 h-4 text-emerald-600" />,
      desc: 'Applies MoRD PMAY-G 25 m²/HH norm with a 100 ha site-planning scale cap. Polygons >100 ha are flagged as terrain screening zones to prevent absurd multi-million population overclaims.',
    },
    {
      title: 'Relocation Planning Horizons (Phase E)',
      icon: <ShieldCheck className="w-4 h-4 text-rose-600" />,
      desc: 'Maps multi-hazard proximity tiers directly to planning categories (Immediate Field Assessment, Short-Term Planning Review, Medium-Term Monitoring, Routine Monitoring) with actionable operational guidance.',
    },
    {
      title: 'Authority Action Center & Export (Phase F)',
      icon: <BookOpenCheck className="w-4 h-4 text-purple-600" />,
      desc: 'Dedicated SDMA/DDMA decision workspace with priority action queue sorted by distance, sub-district/block aggregation table, and one-click printable CSV export.',
    },
  ];

  const limitations = [
    { title: 'Disaster History Ingestion Status', desc: 'Integration schema and validation pipeline are implemented; ingestion of verified historical incident logs from USDMA Dehradun is pending.', tip: 'Schema prepared. Official records pending acquisition.' },
    { title: 'Administrative Centroids vs Settlement Footprints', desc: 'Village coordinates represent administrative reference points. Actual habitations, building clusters, or roads may be closer to hazard terrain than centroid distances indicate.', tip: 'Centroid planar distances are proxy metrics.' },
    { title: 'Census 2011 Baseline Vintage', desc: 'Demographic baseline is from Census 2011 (~15 years old). Demographic expansion and new settlements are not reflected.', tip: 'Population figures represent 2011 baseline.' },
    { title: '30-Meter DEM Spatial Precision', desc: 'Slope and hydrological indices are derived at ~30m pixel resolution. Local site micro-topography requires on-site topographic surveys.', tip: 'Micro-relief variations require total station surveys.' },
    { title: 'Equal-Weight Multi-Hazard Integration', desc: 'Multi-hazard screening integrates terrain susceptibility proxy (50%) and hydrological flood exposure proxy (50%) as an uncalibrated deterministic baseline.', tip: 'Deterministic equal weighting proxy.' },
    { title: 'Preliminary Carrying Capacity Scenarios', desc: 'Capacity estimates reflect PMAY-G minimum built floor area norms (25 m²/HH) and are capped at 100 ha. Detailed engineering, water access, and geotechnical soil surveys are mandatory.', tip: 'Preliminary planning scenarios only.' },
    { title: 'No Automated Settlement Allocation', desc: 'The system identifies topographically feasible areas but does not automatically allocate habitations to sites, preserving human-in-the-loop authority discretion.', tip: 'Official multi-disciplinary planning required.' },
    { title: 'Decision Support Only', desc: 'All outputs are screening tools for directing field survey resources and do not constitute official government evacuation orders or relocation declarations.', tip: 'Requires SDMA/DDMA authorization.' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BookOpenCheck className="w-5 h-5 text-blue-700" />
            <span>Methodology, Provenance & Transparency</span>
          </h2>
          <InfoTooltip
            title="Scientific Methodology Audit"
            content="Complete transparency audit of data provenance, processing pipeline steps, deterministic decision logic, and scientific limitations."
            side="bottom"
          />
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          Deterministic Rule-Based Spatial Architecture & Limitations Audit (SIH26191)
        </p>
      </div>

      {/* Problem Statement Innovations Grid */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            SIH26191 Problem Statement Compliance & Architectural Enhancements
          </h3>
          <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-[10px] font-bold uppercase">
            Phases A–F Complete
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          {innovations.map((inv, idx) => (
            <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-slate-900 text-xs">
                {inv.icon}
                <span>{inv.title}</span>
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                {inv.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Processing Pipeline Architecture (Steps 1–10)
          </h3>
          <InfoTooltip
            title="10-Step Deterministic Pipeline"
            content="Step-by-step reproducible GIS processing from raw DEM to decision-support village profiles."
            side="left"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 1–3</span>
              <InfoTooltip title="DEM Processing" content="Copernicus GLO-30m slope & aspect derivation reprojected to UTM Zone 44N (EPSG:32644)." side="top" />
            </div>
            <p className="font-semibold text-slate-900">DEM Processing</p>
            <p className="text-[11px] text-slate-500 mt-1">Copernicus GLO-30m slope & aspect derivation in UTM 44N</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 4–6</span>
              <InfoTooltip title="Multi-Hazard Screening" content="Equal-weight integration of terrain slope proxy and hydrological Topographic Wetness Index (TWI)." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Multi-Hazard</p>
            <p className="text-[11px] text-slate-500 mt-1">Terrain susceptibility proxy (50%) + Hydrological TWI proxy (50%)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEP 7</span>
              <InfoTooltip title="Candidate Red Zones" content="Extraction of 289 vector polygons representing moderate-to-higher multi-hazard screening zones." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Red Zones</p>
            <p className="text-[11px] text-slate-500 mt-1">289 Candidate Red Zone vector polygons generated</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 8–9</span>
              <InfoTooltip title="Exposure & Terrain" content="Spatial join of 653 Census habitations and screening of 6,823 candidate terrain feasibility clusters (slope ≤ 20°)." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Exposure & Terrain</p>
            <p className="text-[11px] text-slate-500 mt-1">653 Habitations join + 6,823 candidate screened terrain areas</p>
          </div>

          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-700 font-bold block mb-1">STEP 10</span>
              <InfoTooltip title="Decision Engine" content="Deterministic, rule-based tier assignment evaluating distance to red zones and centroid hazard class." side="top" />
            </div>
            <p className="font-semibold text-blue-950">Decision Engine</p>
            <p className="text-[11px] text-blue-800 mt-1">Explainable rule-based priority tiers & relocation horizons</p>
          </div>
        </div>
      </div>

      {/* Data Availability Matrix */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Dataset Acquisition & Availability Matrix
          </h3>
          <InfoTooltip
            title="Data Provenance Matrix"
            content="Tracks which datasets are ingested into the platform vs pending official acquisition from departments."
            side="left"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-700 font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Dataset Name</span>
                    <InfoTooltip title="Dataset Name" content="Name of the spatial or demographic dataset." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Source / Citation</span>
                    <InfoTooltip title="Data Source" content="Publishing agency or open data repository." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Status</span>
                    <InfoTooltip title="Acquisition Status" content="AVAILABLE = active; NOT_ACQUIRED = pending department release." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Pipeline Role</span>
                    <InfoTooltip title="Pipeline Role" content="How this dataset is utilized in the decision-support engine." side="top" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {dataMatrix.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 font-semibold text-slate-900">
                    <div className="flex items-center gap-1">
                      <span>{item.name}</span>
                      <InfoTooltip title={item.name} content={item.tip} side="right" />
                    </div>
                  </td>
                  <td className="py-2.5 px-4 text-slate-600">{item.source}</td>
                  <td className="py-2.5 px-4">
                    <StatusBadge status={item.status} size="sm" />
                  </td>
                  <td className="py-2.5 px-4 text-slate-600">{item.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Limitations Accordion / Cards */}
      <div id="limitations" className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Scientific Caveats & Limitations</span>
          </h3>
          <InfoTooltip
            title="Scientific Caveats"
            content="Essential scientific and administrative caveats that evaluators and planners must review."
            side="left"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {limitations.map((lim, idx) => (
            <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1 relative group">
              <div className="flex items-center justify-between">
                <p className="font-bold text-slate-900">{idx + 1}. {lim.title}</p>
                <InfoTooltip title={lim.title} content={lim.tip} side="top" />
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">{lim.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
