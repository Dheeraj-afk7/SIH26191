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
  ChevronRight
} from 'lucide-react';
import { PROJECT_INFO } from '../../config/constants';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
  step?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/',
    label: 'Executive Dashboard',
    icon: LayoutDashboard,
    step: '01',
  },
  {
    path: '/map',
    label: 'Interactive GIS Map',
    icon: Map,
    step: '02',
  },
  {
    path: '/villages',
    label: 'Village Explorer',
    icon: Building2,
    badge: '653',
    step: '03',
  },
  {
    path: '/candidate-areas',
    label: 'Candidate Areas',
    icon: Layers,
    badge: '5',
    step: '04',
  },
  {
    path: '/methodology',
    label: 'Methodology & Transparency',
    icon: BookOpenCheck,
    step: '05',
  },
  {
    path: '/status',
    label: 'System & Data Status',
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
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-3 border-b border-navy-800 bg-navy-950/40 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
            <ShieldAlert className="w-4.5 h-4.5" />
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-bold tracking-tight text-white truncate leading-none">
                {PROJECT_INFO.PILOT_DISTRICT}
              </h1>
              <p className="text-[10px] text-blue-300 font-semibold uppercase tracking-widest truncate mt-0.5">
                Decision Support
              </p>
            </div>
          )}
        </div>

        <button
          onClick={onToggleCollapse}
          className="text-slate-400 hover:text-white p-1.5 rounded-md hover:bg-navy-800 transition-colors shrink-0"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {!isCollapsed && (
          <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500 px-3 pb-2 pt-1">
            Navigation
          </p>
        )}
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-blue-600/20 text-white font-bold border border-blue-500/30 shadow-sm'
                    : 'text-slate-300 hover:bg-navy-800/80 hover:text-white font-medium'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                    isActive ? 'text-blue-400' : 'text-slate-400 group-hover:text-blue-300'
                  }`} />
                  {!isCollapsed && (
                    <>
                      <span className="truncate flex-1">{item.label}</span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {item.badge && (
                          <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${
                            isActive
                              ? 'bg-blue-500/30 text-blue-200 border border-blue-400/30'
                              : 'bg-navy-800 text-slate-400 border border-navy-700'
                          }`}>
                            {item.badge}
                          </span>
                        )}
                      </div>
                    </>
                  )}

                  {/* Active indicator dot */}
                  {isActive && !isCollapsed && (
                    <span className="absolute right-2.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-blue-400 shadow-glow" />
                  )}

                  {/* Tooltip for collapsed view */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-slate-900 text-white text-xs rounded-lg shadow-lg whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 border border-slate-700">
                      {item.label}
                      {item.badge && (
                        <span className="ml-1.5 text-slate-400">({item.badge})</span>
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
              <span className="text-[10px] px-1.5 py-0.5 bg-blue-900/60 text-blue-300 rounded border border-blue-800/50 font-semibold">
                v{PROJECT_INFO.PIPELINE_VERSION}
              </span>
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
