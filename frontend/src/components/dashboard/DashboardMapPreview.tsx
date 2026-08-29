import React, { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, GeoJSON, Popup } from 'react-leaflet';
import { Map, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useVillages, useRedZones } from '../../hooks';
import { MAP_DEFAULTS } from '../../config/constants';
import { getTierConfig } from '../../utils/tierUtils';
import { formatNumber, formatDistance } from '../../utils/formatters';
import { reprojectGeoJson, toLeafletLatLng } from '../../utils/projection';
import { PriorityBadge } from '../shared/PriorityBadge';

export const DashboardMapPreview: React.FC = () => {
  const { data: rawVillageCollection } = useVillages({ limit: 700 });
  const { data: rawRedZonesCollection } = useRedZones();

  const redZonesCollection = useMemo(() => {
    return rawRedZonesCollection ? reprojectGeoJson(rawRedZonesCollection) : null;
  }, [rawRedZonesCollection]);

  const villages = rawVillageCollection?.features || [];

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[380px]">
      {/* Header Bar */}
      <div className="p-3 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Map className="w-4 h-4 text-blue-600" />
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            District Spatial Preview
          </h3>
        </div>
        <Link
          to="/map"
          className="text-xs font-semibold text-blue-700 hover:text-blue-900 inline-flex items-center gap-1"
        >
          <span>Open Full GIS Map</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Map Area */}
      <div className="relative flex-1 w-full bg-slate-100">
        <MapContainer
          center={MAP_DEFAULTS.RUDRAPRAYAG_CENTER}
          zoom={9}
          minZoom={8}
          maxZoom={12}
          scrollWheelZoom={false}
          className="w-full h-full z-0"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Red Zones (simplified fill) */}
          {redZonesCollection && (
            <GeoJSON
              key="dashboard-red-zones"
              data={redZonesCollection as any}
              style={{
                color: '#DC2626',
                weight: 1,
                fillColor: '#DC2626',
                fillOpacity: 0.3,
              }}
            />
          )}

          {/* Villages */}
          {villages.map((village) => {
            const rawCoords = village.geometry.coordinates as [number, number];
            const [lat, lon] = toLeafletLatLng(rawCoords);
            const p = village.properties;
            const config = getTierConfig(p.priority_tier);

            return (
              <CircleMarker
                key={p.village_id}
                center={[lat, lon]}
                radius={config.mapSize * 0.8}
                pathOptions={{
                  fillColor: config.mapColor,
                  fillOpacity: 0.9,
                  color: '#FFFFFF',
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="text-xs space-y-1 p-0.5">
                    <div className="flex items-center justify-between gap-2">
                      <strong className="text-slate-900">{p.village_name}</strong>
                      <PriorityBadge tier={p.priority_tier} size="sm" />
                    </div>
                    <p className="text-[11px] text-slate-600">
                      Pop: {formatNumber(p.tot_pop)} · Dist: {formatDistance(p.nearest_hazard_distance_m)}
                    </p>
                    <Link
                      to={`/villages/${p.village_id}`}
                      className="block text-center text-[10px] text-blue-600 font-bold hover:underline pt-1"
                    >
                      View Profile →
                    </Link>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>

        {/* Small floating hint */}
        <div className="absolute bottom-2 left-2 z-[500] bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] text-slate-600 border border-slate-200">
          Pan / zoom preview · Click marker for village info
        </div>
      </div>
    </div>
  );
};
