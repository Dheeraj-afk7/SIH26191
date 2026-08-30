import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, GeoJSON, Popup } from 'react-leaflet';
import type { Map as LeafletMap } from 'leaflet';
import { Layers, RotateCcw, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useVillages, useRedZones, useCandidateAreas, useInfrastructure, useDisasters, useRoads } from '../../hooks';
import { MAP_DEFAULTS, PRIORITY_TIERS, PriorityTierKey } from '../../config/constants';
import { getTierConfig } from '../../utils/tierUtils';
import { formatNumber, formatDistance, formatHectares } from '../../utils/formatters';
import { reprojectGeoJson, toLeafletLatLng } from '../../utils/projection';
import { MapLegend } from './MapLegend';
import { PriorityBadge } from '../shared/PriorityBadge';
import { InfoTooltip } from '../shared/InfoTooltip';

export const GisMap: React.FC = () => {
  const [map, setMap] = useState<LeafletMap | null>(null);
  const [bbox, setBbox] = useState<string | undefined>(undefined);
  
  // Decision-Modulating Layer Visibility
  const [showRedZones, setShowRedZones] = useState(true);
  const [showCandidateAreas, setShowCandidateAreas] = useState(true);
  const [activeTiers, setActiveTiers] = useState<Record<PriorityTierKey, boolean>>({
    Tier1_AttentionPriority: true,
    Tier2_ElevatedAttention: true,
    Tier3_Monitoring: true,
    BeyondProximity: true,
  });

  // Contextual Reference Layer Visibility (Non-Modulating)
  const [showInfrastructure, setShowInfrastructure] = useState(true);
  const [showDisasters, setShowDisasters] = useState(true);
  const [showRoads, setShowRoads] = useState(true);

  // Data fetching from backend
  const { data: rawVillageCollection } = useVillages({ limit: 700 });
  const { data: rawRedZonesCollection } = useRedZones();
  const { data: rawCandidateAreasCollection } = useCandidateAreas({ bbox, limit: 50 });
  const { data: rawInfrastructureCollection } = useInfrastructure({ limit: 350 });
  const { data: rawDisasterCollection } = useDisasters({ limit: 50 });
  const { data: rawRoadCollection } = useRoads({ arterial_only: true, limit: 500 });

  // Reproject layers from UTM Zone 44N (EPSG:32644) to EPSG:4326 for Leaflet rendering
  const redZonesCollection = useMemo(() => {
    return rawRedZonesCollection ? reprojectGeoJson(rawRedZonesCollection) : null;
  }, [rawRedZonesCollection]);

  const candidateAreasCollection = useMemo(() => {
    return rawCandidateAreasCollection ? reprojectGeoJson(rawCandidateAreasCollection) : null;
  }, [rawCandidateAreasCollection]);

  const villages = rawVillageCollection?.features || [];
  const filteredVillages = villages.filter(
    (v) => activeTiers[v.properties.priority_tier as PriorityTierKey]
  );

  const infrastructureFeatures = rawInfrastructureCollection?.features || [];
  const disasterFeatures = rawDisasterCollection?.features || [];

  const toggleTier = (tierKey: PriorityTierKey) => {
    setActiveTiers((prev) => ({ ...prev, [tierKey]: !prev[tierKey] }));
  };

  // Sync BBox when map moves
  useEffect(() => {
    if (!map) return;

    const updateBounds = () => {
      const bounds = map.getBounds();
      const bboxStr = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
      setBbox(bboxStr);
    };

    updateBounds();
    map.on('moveend', updateBounds);
    return () => {
      map.off('moveend', updateBounds);
    };
  }, [map]);

  const handleResetView = () => {
    if (map) {
      map.flyTo(MAP_DEFAULTS.RUDRAPRAYAG_CENTER, MAP_DEFAULTS.DEFAULT_ZOOM, { duration: 1 });
    }
  };

  const getInfraColor = (broadType: string, isPotential: boolean, isEvidenced: boolean) => {
    if (isEvidenced) return '#1E3A8A'; // Evidenced Police / Fire
    if (isPotential) return '#7C3AED'; // Hospital / CHC / PHC
    if (broadType === 'HEALTHCARE') return '#0D9488'; // Subcentre / Clinic
    if (broadType === 'EDUCATION') return '#2563EB'; // School / College
    return '#64748B'; // Civic / Admin
  };

  return (
    <div className="relative w-full h-[720px] bg-slate-100 rounded-xl overflow-hidden border border-slate-200 shadow-sm flex flex-col">
      {/* Top Floating Control Bar */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2 max-w-[95%]">
        {/* Row 1: Decision-Modulating Layers & Tiers */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Decision Layers Pill */}
          <div className="bg-white/95 backdrop-blur-sm p-1.5 px-3 rounded-lg border border-slate-200 shadow-md flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1 font-bold text-slate-800">
              <Layers className="w-3.5 h-3.5 text-blue-600" />
              <span className="hidden sm:inline">Core Decision:</span>
              <InfoTooltip
                title="Core Decision-Modulating Layers"
                content="Directly determine or represent priority tiers, hazard screening zones, and relocation candidate terrain."
                side="bottom"
              />
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer select-none text-slate-700 font-medium hover:text-slate-900">
              <input
                type="checkbox"
                checked={showRedZones}
                onChange={(e) => setShowRedZones(e.target.checked)}
                className="rounded text-red-600 focus:ring-red-500 w-3.5 h-3.5"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-sm bg-red-600 inline-block" />
                <span>Red Zones (289)</span>
              </span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer select-none text-slate-700 font-medium hover:text-slate-900">
              <input
                type="checkbox"
                checked={showCandidateAreas}
                onChange={(e) => setShowCandidateAreas(e.target.checked)}
                className="rounded text-amber-600 focus:ring-amber-500 w-3.5 h-3.5"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block" />
                <span>Candidate Terrain</span>
              </span>
            </label>
          </div>

          {/* Tier Toggles */}
          <div className="bg-white/95 backdrop-blur-sm p-1.5 px-2.5 rounded-lg border border-slate-200 shadow-md flex items-center gap-1.5 text-xs">
            <span className="text-[11px] font-semibold text-slate-500 mr-1 hidden md:inline">Tiers:</span>
            {(Object.keys(PRIORITY_TIERS) as PriorityTierKey[]).map((tierKey) => {
              const config = PRIORITY_TIERS[tierKey];
              const isActive = activeTiers[tierKey];
              return (
                <button
                  key={tierKey}
                  onClick={() => toggleTier(tierKey)}
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold border transition-all ${
                    isActive
                      ? `${config.badgeBg} ${config.badgeText} ${config.badgeBorder} shadow-xs`
                      : 'bg-slate-100 text-slate-400 border-slate-200 line-through opacity-60'
                  }`}
                  title={config.label}
                >
                  {config.shortLabel}
                </button>
              );
            })}
          </div>
        </div>

        {/* Row 2: Contextual Reference Layers (Non-Modulating) */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="bg-slate-900/90 text-white backdrop-blur-sm p-1.5 px-3 rounded-lg border border-slate-700 shadow-md flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1 font-bold text-slate-200">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Contextual Lifelines:</span>
              <InfoTooltip
                title="Contextual Reference Layers"
                content="Environmental and infrastructure metrics for planning reference. These layers DO NOT alter deterministic priority tiers."
                side="bottom"
              />
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer select-none text-slate-200 font-medium hover:text-white">
              <input
                type="checkbox"
                checked={showInfrastructure}
                onChange={(e) => setShowInfrastructure(e.target.checked)}
                className="rounded text-teal-500 focus:ring-teal-400 w-3.5 h-3.5"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-400 inline-block" />
                <span>Facilities (291)</span>
              </span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer select-none text-slate-200 font-medium hover:text-white">
              <input
                type="checkbox"
                checked={showDisasters}
                onChange={(e) => setShowDisasters(e.target.checked)}
                className="rounded text-orange-500 focus:ring-orange-400 w-3.5 h-3.5"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400 inline-block" />
                <span>Disaster History (22)</span>
              </span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer select-none text-slate-200 font-medium hover:text-white">
              <input
                type="checkbox"
                checked={showRoads}
                onChange={(e) => setShowRoads(e.target.checked)}
                className="rounded text-blue-400 focus:ring-blue-300 w-3.5 h-3.5"
              />
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-blue-400 inline-block" />
                <span>Arterial Roads</span>
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* Reset View Button Top Right */}
      <div className="absolute top-3 right-3 z-[1000] flex items-center gap-1">
        <button
          onClick={handleResetView}
          className="p-2 bg-white/95 backdrop-blur-sm rounded-lg border border-slate-300 shadow-md text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center"
          title="Reset View to Rudraprayag Extent"
          aria-label="Reset View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom Left Legend */}
      <div className="absolute bottom-6 left-3 z-[1000]">
        <MapLegend
          showRedZones={showRedZones}
          showCandidateAreas={showCandidateAreas}
          showInfrastructure={showInfrastructure}
          showDisasters={showDisasters}
          showRoads={showRoads}
        />
      </div>

      {/* Bottom Right Warning Watermark */}
      <div className="absolute bottom-2 right-3 z-[1000] bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded text-[10px] text-slate-600 border border-slate-200 shadow-xs pointer-events-none">
        <span>Preliminary Decision Support · Contextual Lifelines Active · Not an Official Certification</span>
      </div>

      {/* The Leaflet Map Instance */}
      <MapContainer
        ref={setMap}
        center={MAP_DEFAULTS.RUDRAPRAYAG_CENTER}
        zoom={MAP_DEFAULTS.DEFAULT_ZOOM}
        minZoom={MAP_DEFAULTS.MIN_ZOOM}
        maxZoom={MAP_DEFAULTS.MAX_ZOOM}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* 1. Arterial Highway Corridors (Phase 2 Routable Roads) */}
        {showRoads && rawRoadCollection && (
          <GeoJSON
            key="arterial-roads-layer"
            data={rawRoadCollection as any}
            style={{
              color: '#2563EB',
              weight: 2.5,
              opacity: 0.85,
            }}
            onEachFeature={(feature, layer) => {
              const p = feature.properties || {};
              layer.bindPopup(`
                <div class="text-xs p-1 space-y-1">
                  <div class="font-bold text-blue-700">
                    <span>${p.name || 'Unnamed Highway'} ${p.ref ? `(${p.ref})` : ''}</span>
                  </div>
                  <div class="text-[11px] text-slate-600">
                    <div>Class: <strong>${p.highway}</strong> | Surface: <strong>${p.surface}</strong></div>
                    <div>Assumed Speed: <strong>${p.assumed_speed_kmh} km/h</strong></div>
                  </div>
                  <p class="text-[10px] text-slate-500 bg-slate-50 p-1 rounded border border-slate-200">
                    Phase 2 Routable Arterial Highway Network (EPSG:32644).
                  </p>
                </div>
              `);
            }}
          />
        )}

        {/* 2. Candidate Hazard-Based Red Zones Layer (289 Polygons) */}
        {showRedZones && redZonesCollection && (
          <GeoJSON
            key="red-zones-layer"
            data={redZonesCollection as any}
            style={{
              color: '#DC2626',
              weight: 1.5,
              fillColor: '#DC2626',
              fillOpacity: 0.35,
            }}
            onEachFeature={(feature, layer) => {
              const props = feature.properties || {};
              layer.bindPopup(`
                <div class="text-xs p-1 space-y-1">
                  <div class="flex items-center gap-1 font-bold text-red-700">
                    <span>Candidate Red Zone: ${props.zone_id || 'RZ'}</span>
                  </div>
                  <p class="text-slate-600 text-[11px] leading-tight">
                    Candidate multi-hazard screening zone derived from slope and flood exposure proxies.
                  </p>
                  <p class="text-[10px] text-red-800 bg-red-50 p-1 rounded border border-red-200 mt-1">
                    ⚠ Requires official geotechnical verification.
                  </p>
                </div>
              `);
            }}
          />
        )}

        {/* 3. Candidate Topographically Feasible Areas Layer (Attributed Polygons with BBox) */}
        {showCandidateAreas && candidateAreasCollection && (
          <GeoJSON
            key={`candidate-areas-${bbox}`}
            data={candidateAreasCollection as any}
            style={{
              color: '#D97706',
              weight: 2,
              dashArray: '4, 4',
              fillColor: '#F59E0B',
              fillOpacity: 0.18,
            }}
            onEachFeature={(feature, layer) => {
              const props = feature.properties || {};
              layer.bindPopup(`
                <div class="text-xs p-1 space-y-1.5 max-w-[240px]">
                  <div class="flex items-center justify-between">
                    <span class="font-mono font-bold text-amber-900 bg-amber-100 px-1.5 py-0.5 rounded">${props.area_id}</span>
                    <span class="text-[10px] text-slate-500 font-mono">${formatHectares(props.area_hectares)}</span>
                  </div>
                  <p class="text-slate-700 text-[11px] font-medium leading-tight">
                    ${(props.area_hectares || 0) > 100 ? 'Large Terrain Screening Zone' : 'Candidate Feasible Terrain Cluster'}
                  </p>
                  <div class="text-[10px] text-slate-600 divide-y divide-slate-100">
                    <div class="py-0.5 flex justify-between"><span>Mean Slope:</span> <strong>${props.mean_slope ? props.mean_slope.toFixed(1) : '—'}°</strong></div>
                    <div class="py-0.5 flex justify-between"><span>Nearest Habitation:</span> <strong>${props.nearest_village_name || '—'}</strong></div>
                  </div>
                  <p class="text-[10px] text-amber-900 bg-amber-50 p-1 rounded border border-amber-300">
                    ⚠ Candidate context only. NOT an approved or recommended relocation site.
                  </p>
                </div>
              `);
            }}
          />
        )}

        {/* 4. Historical Disaster Incidents (22 Canonical Literature Curated Events) */}
        {showDisasters && disasterFeatures.map((event) => {
          const coords = event.geometry.coordinates as [number, number];
          const p = event.properties;
          const isLandslide = p.hazard_type === 'LANDSLIDE';

          return (
            <CircleMarker
              key={p.canonical_incident_id}
              center={[coords[1], coords[0]]}
              radius={6}
              pathOptions={{
                fillColor: isLandslide ? '#EA580C' : '#0284C7',
                fillOpacity: 0.9,
                color: '#FFFFFF',
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="text-xs space-y-1.5 p-1 min-w-[240px]">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-1">
                    <span className="font-bold text-slate-900">{p.location_name} ({p.year})</span>
                    <span className="text-[10px] font-mono px-1 rounded bg-slate-100 text-slate-700">{p.canonical_incident_id}</span>
                  </div>
                  <div className="text-[11px] text-slate-700 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Hazard Type:</span>
                      <strong>{p.hazard_type}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Recorded Fatalities:</span>
                      <strong className="text-red-700">{p.fatalities}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Coordinate Uncertainty:</span>
                      <strong className="font-mono text-amber-800">±{p.coordinate_uncertainty_m} m ({p.uncertainty_band})</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Evidence Level:</span>
                      <span className="font-semibold text-blue-800">{p.evidence_level}</span>
                    </div>
                    <div className="text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-200 mt-1">
                      <div className="font-medium truncate" title={p.source_document_title}>
                        Doc: {p.source_document_title || p.source_provider}
                      </div>
                      <div className="text-[9px] text-slate-400 mt-0.5 italic">
                        Verified secondary literature record · Geometry not independently resurveyed
                      </div>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* 5. Critical Infrastructure Facilities (291 OSM Features) */}
        {showInfrastructure && infrastructureFeatures.map((fac) => {
          const coords = fac.geometry.coordinates as [number, number];
          const p = fac.properties;
          const color = getInfraColor(
            p.facility_broad_type,
            p.potential_emergency_receiving_facility,
            p.explicitly_evidenced_emergency_capability
          );

          return (
            <CircleMarker
              key={p.facility_id}
              center={[coords[1], coords[0]]}
              radius={4.5}
              pathOptions={{
                fillColor: color,
                fillOpacity: 0.9,
                color: '#FFFFFF',
                weight: 1.2,
              }}
            >
              <Popup>
                <div className="text-xs space-y-1 p-1 min-w-[210px]">
                  <div className="font-bold text-slate-900 border-b border-slate-100 pb-1">
                    {p.name}
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-0.5">
                    <div>Category: <strong>{p.facility_category.replace(/_/g, ' ')}</strong></div>
                    <div>Type: <strong>{p.facility_broad_type}</strong></div>
                    <div>OSM Native ID: <code className="text-[10px] bg-slate-100 px-1 rounded">{p.osm_id}</code></div>
                    {p.explicitly_evidenced_emergency_capability ? (
                      <div className="text-[10px] text-blue-800 font-semibold bg-blue-50 p-1 rounded border border-blue-200">
                        ✓ Explicitly Evidenced Emergency Facility
                      </div>
                    ) : p.potential_emergency_receiving_facility ? (
                      <div className="text-[10px] text-purple-800 font-semibold bg-purple-50 p-1 rounded border border-purple-200">
                        ⚡ Potential Emergency Receiving Clinical Facility
                      </div>
                    ) : null}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* 6. Habitations / Village Priority Points (653 Centroids Reprojected to Lat/Lon) */}
        {filteredVillages.map((village) => {
          const rawCoords = village.geometry.coordinates as [number, number];
          const [lat, lon] = toLeafletLatLng(rawCoords);
          const p = village.properties;
          const config = getTierConfig(p.priority_tier);

          return (
            <CircleMarker
              key={p.village_id}
              center={[lat, lon]}
              radius={config.mapSize}
              pathOptions={{
                fillColor: config.mapColor,
                fillOpacity: 0.95,
                color: '#FFFFFF',
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="text-xs space-y-2 p-1 min-w-[220px]">
                  <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1.5">
                    <div>
                      <p className="font-bold text-slate-900 text-sm">{p.village_name}</p>
                      <p className="text-[10px] text-slate-500 font-mono">ID: #{p.village_id}</p>
                    </div>
                    <PriorityBadge tier={p.priority_tier} size="sm" />
                  </div>

                  <div className="space-y-1 text-slate-700 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Population (2011):</span>
                      <span className="font-semibold">{formatNumber(p.tot_pop)} ({p.households} HH)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Dist to Red Zone:</span>
                      <span className="font-semibold font-mono text-red-700">
                        {formatDistance(p.nearest_hazard_distance_m)} ({p.nearest_zone_id})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Nearest Health Facility:</span>
                      <span className="font-semibold">{formatDistance(p.dist_to_nearest_health_facility_m)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Road Snapping Dist:</span>
                      <span className="font-semibold">{formatDistance(p.road_snapping_distance_m)}</span>
                    </div>
                  </div>

                  {p.priority_reason && (
                    <p className="text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-200 leading-snug">
                      {p.priority_reason}
                    </p>
                  )}

                  <div className="pt-1">
                    <Link
                      to={`/villages/${p.village_id}`}
                      className="block text-center w-full py-1 px-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                    >
                      View Full Decision Profile →
                    </Link>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};
