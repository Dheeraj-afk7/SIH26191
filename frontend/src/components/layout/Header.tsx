import React from 'react';
import { Menu, BookOpen, ExternalLink } from 'lucide-react';
import { useHealth } from '../../hooks';
import { Link } from 'react-router-dom';
import { InfoTooltip } from '../shared/InfoTooltip';

interface HeaderProps {
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileMenu }) => {
  const { data: health, isLoading } = useHealth();

  const isHealthy = health?.status === 'ok';

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between shadow-sm z-20 shrink-0">
      {/* Left: Mobile Toggle & Title */}
      <div className="flex items-center gap-3">
        {onToggleMobileMenu && (
          <div className="flex items-center gap-1 md:hidden">
            <button
              onClick={onToggleMobileMenu}
              className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Toggle navigation drawer"
            >
              <Menu className="w-5 h-5" />
            </button>
            <InfoTooltip
              title="Navigation Menu"
              content="Toggle the mobile drawer to navigate across Executive Dashboard, GIS Map, Village Explorer, Candidate Areas, and Methodology."
              side="bottom"
            />
          </div>
        )}

        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-sm md:text-base">
              Rudraprayag District
            </span>
            <div className="flex items-center gap-1">
              <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-800 border border-blue-200 rounded">
                SIH26191 Pilot
              </span>
              <InfoTooltip
                title="SIH26191 Pilot System"
                content="Deterministic GIS-based decision support prototype for hazard red zones and relocation feasibility screening across Rudraprayag District, Uttarakhand."
                note="Pilot decision-support platform for disaster management authorities."
                side="bottom"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Right: Health pill & Links */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Backend API Health indicator */}
        <div className="flex items-center gap-1">
          <Link
            to="/status"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isLoading
                  ? 'bg-amber-400 animate-pulse'
                  : isHealthy
                  ? 'bg-emerald-500'
                  : 'bg-rose-500'
              }`}
            />
            <span className="hidden sm:inline text-slate-600">API Status:</span>
            <span className="font-semibold text-slate-900">
              {isLoading ? 'Checking' : isHealthy ? 'Online' : 'Offline'}
            </span>
          </Link>
          <InfoTooltip
            title="Backend API Connection"
            content="Real-time connection status to the FastAPI backend service (data loader in-memory spatial cache, village attributes, and red zone layers)."
            formula="GET /api/health -> 200 OK"
            side="bottom"
          />
        </div>

        {/* Methodology Shortcut */}
        <div className="hidden md:flex items-center gap-1">
          <Link
            to="/methodology"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded border border-slate-200 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            <span>Methodology</span>
          </Link>
          <InfoTooltip
            title="Methodology & Transparency"
            content="Inspect the complete 10-step GIS pipeline, data provenance matrix, screening rules, and scientific caveats."
            side="bottom"
          />
        </div>

        {/* Documentation / API link */}
        <div className="hidden lg:flex items-center gap-1">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            <span>FastAPI Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <InfoTooltip
            title="FastAPI Swagger OpenAPI Docs"
            content="Opens the interactive REST API documentation with live endpoints for /api/villages, /api/red-zones, /api/candidate-areas, and /api/decision/summary."
            side="bottom"
          />
        </div>
      </div>
    </header>
  );
};
