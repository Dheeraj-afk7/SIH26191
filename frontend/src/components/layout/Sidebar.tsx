import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Map, 
  Building2, 
  Layers, 
  BookOpenCheck, 
  Activity,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Shield,
  RefreshCw
} from 'lucide-react';
import { PROJECT_INFO } from '../../config/constants';
import { InfoTooltip } from '../shared/InfoTooltip';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  path: string;
  label: string;
  description: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
  step?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/',
    label: 'Executive Dashboard',
    description: 'High-level overview of habitations, hazard proximity tiers, and executive KPI metrics.',
    icon: LayoutDashboard,
    step: '01',
  },
  {
    path: '/map',
    label: 'Interactive GIS Map',
    description: 'Multi-layer spatial viewer with 289 candidate red zones, 653 habitations, and candidate terrain.',
    icon: Map,
    step: '02',
  },
  {
    path: '/villages',
    label: 'Village Explorer',
    description: 'Searchable directory of 653 habitations with filterable priority tiers & decision profiles.',
    icon: Building2,
    badge: '653',
    step: '03',
  },
  {
    path: '/candidate-areas',
    label: 'Candidate Areas',
    description: '6,823 terrain-screened polygons (slope ≤ 20°). Displaying top areas by size. All require field verification.',
    icon: Layers,
    badge: '6823',
    step: '04',
  },
  {
    path: '/methodology',
    label: 'Methodology & Audit',
    description: 'Full audit of deterministic 10-step pipeline rules, data provenance matrix, and caveats.',
    icon: BookOpenCheck,
    step: '05',
  },
  {
    path: '/authority',
    label: 'Authority Action Center',
    description: 'SDMA/DDMA priority action queue, block-level summary, and CSV export for district planning.',
    icon: Shield,
    badge: '!',
    step: '06',
  },
  {
    path: '/pipeline',
    label: 'Pipeline Recompute',
    description: 'Operator-triggered workflow to recompute classifications after threshold or data updates.',
    icon: RefreshCw,
  },
  {
    path: '/status',
    label: 'System & Data Status',
    description: 'Real-time FastAPI backend diagnostics and in-memory spatial cache status.',
    icon: Activity,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
}) => {
  return (
    <aside
      className={`bg-navy-900 text-slate-100 flex flex-col transition-all duration-300 border-r border-navy-800 shadow-nav z-30 shrink-0 select-none ${
        isCollapsed ? 'w-16' : 'w-72'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-3.5 border-b border-navy-800 bg-navy-950/50 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
            <ShieldAlert className="w-4.5 h-4.5" />
          </div>
          {!isCollapsed && (
            <div className="min-w-0 flex items-center gap-1.5">
              <div className="min-w-0">
                <h1 className="text-sm font-bold tracking-tight text-white truncate leading-none">
                  {PROJECT_INFO.PILOT_DISTRICT}
                </h1>
                <p className="text-[10px] text-blue-300 font-semibold uppercase tracking-widest truncate mt-0.5">
                  Decision Support
                </p>
              </div>
              <InfoTooltip
                title="Rudraprayag Decision Support"
                content="GIS-informed decision-support platform assisting disaster management authorities in hazard red zone identification and relocation screening."
                side="right"
                triggerClassName="text-slate-400 hover:text-white"
              />
            </div>
          )}
        </div>

        <div className="flex items-center">
          <button
            onClick={onToggleCollapse}
            className="text-slate-400 hover:text-white p-1.5 rounded-md hover:bg-navy-800 transition-colors shrink-0"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {!isCollapsed && (
          <div className="flex items-center justify-between px-3 pb-1.5 pt-1">
            <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400">
              Navigation Pages
            </p>
            <InfoTooltip
              title="Platform Navigation"
              content="Use these navigation buttons to explore executive summaries, spatial maps, village registers, candidate areas, authority workflows, and scientific methodology."
              side="right"
              triggerClassName="text-slate-500 hover:text-slate-300"
            />
          </div>
        )}
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-blue-600/20 text-white font-semibold border-l-[3px] border-l-blue-500 border border-blue-500/20 shadow-sm'
                    : 'text-slate-300 hover:bg-navy-800/80 hover:text-white font-medium border-l-[3px] border-l-transparent'
                } ${isCollapsed ? 'justify-center px-2' : ''}`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                    isActive ? 'text-blue-400' : 'text-slate-400 group-hover:text-blue-300'
                  }`} />
                  {!isCollapsed && (
                    <>
                      <span className="truncate flex-1 text-left">{item.label}</span>
                      <div className="flex items-center gap-1.5 shrink-0 ml-auto">
                        {item.badge && (
                          <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${
                            item.badge === '!'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : isActive
                              ? 'bg-blue-500/30 text-blue-200 border border-blue-400/30'
                              : 'bg-navy-800 text-slate-400 border border-navy-700'
                          }`}>
                            {item.badge}
                          </span>
                        )}
                        <InfoTooltip
                          title={item.label}
                          content={item.description}
                          side="right"
                          triggerClassName="text-slate-400 group-hover:text-slate-200 opacity-70 group-hover:opacity-100"
                        />
                      </div>
                    </>
                  )}

                  {/* Tooltip for collapsed view */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-3 px-3 py-2 bg-slate-900 text-white text-xs rounded-xl shadow-2xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 border border-slate-700">
                      <p className="font-bold">{item.label}</p>
                      <p className="text-[10px] text-slate-300 max-w-xs whitespace-normal mt-0.5">{item.description}</p>
                      {item.badge && (
                        <span className="mt-1.5 inline-block text-[10px] text-blue-300 font-mono">Count / Tag: {item.badge}</span>
                      )}
                    </div>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      {!isCollapsed && (
        <div className="p-3 border-t border-navy-800/60">
          <div className="p-3 rounded-lg bg-navy-950/60 border border-navy-800 text-[11px] text-slate-400">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-slate-300">{PROJECT_INFO.ID}</span>
              <div className="flex items-center gap-1">
                <span className="text-[10px] px-1.5 py-0.5 bg-blue-900/60 text-blue-300 rounded border border-blue-800/50 font-semibold">
                  v{PROJECT_INFO.PIPELINE_VERSION}
                </span>
                <InfoTooltip
                  title="Pipeline Version v1.0"
                  content="Deterministic static snapshot pipeline incorporating Census 2011 demographics, Copernicus GLO-30 DEM, and SHRUG v2.2 centroids."
                  side="top"
                  triggerClassName="text-slate-400 hover:text-white"
                />
              </div>
            </div>
            <p className="text-[10px] text-slate-500 truncate">
              {PROJECT_INFO.STATE}, India · Pilot System
            </p>
          </div>
        </div>
      )}
    </aside>
  );
};
