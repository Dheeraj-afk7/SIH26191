import React from 'react';
import { Menu, BookOpen, ExternalLink } from 'lucide-react';
import { useHealth } from '../../hooks';
import { Link } from 'react-router-dom';

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
          <button
            onClick={onToggleMobileMenu}
            className="md:hidden p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-sm md:text-base">
              Rudraprayag District
            </span>
            <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-800 border border-blue-200 rounded">
              SIH26191 Pilot
            </span>
          </div>
        </div>
      </div>

      {/* Right: Health pill & Links */}
      <div className="flex items-center gap-3">
        {/* Backend API Health indicator */}
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

        {/* Methodology Shortcut */}
        <Link
          to="/methodology"
          className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded border border-slate-200 transition-colors"
        >
          <BookOpen className="w-3.5 h-3.5 text-blue-600" />
          <span>Methodology</span>
        </Link>

        {/* Documentation / API link */}
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden lg:inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <span>FastAPI Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
};
