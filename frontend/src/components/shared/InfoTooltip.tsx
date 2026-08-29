import React, { useState, useRef, useEffect } from 'react';
import { Info, HelpCircle } from 'lucide-react';

export interface InfoTooltipProps {
  title?: string;
  content: string;
  formula?: string;
  note?: string;
  side?: 'top' | 'bottom' | 'left' | 'right' | 'auto';
  align?: 'start' | 'center' | 'end';
  icon?: 'info' | 'help';
  size?: 'xs' | 'sm' | 'md';
  className?: string;
  triggerClassName?: string;
  children?: React.ReactNode;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({
  title,
  content,
  formula,
  note,
  side = 'top',
  icon = 'info',
  size = 'xs',
  className = '',
  triggerClassName = '',
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node) &&
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target as Node)
      ) {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isVisible]);

  // Handle keyboard escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isVisible]);

  const sizeClasses = {
    xs: 'w-3.5 h-3.5',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
  }[size];

  // Position classes
  const positionClasses = {
    top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
    bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
    left: 'right-full mr-2 top-1/2 -translate-y-1/2',
    right: 'left-full ml-2 top-1/2 -translate-y-1/2',
    auto: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
  }[side];

  const IconComponent = icon === 'help' ? HelpCircle : Info;

  return (
    <div
      ref={triggerRef}
      className={`relative inline-flex items-center align-middle ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {/* Trigger */}
      <button
        type="button"
        aria-label={title || 'Information'}
        onClick={(e) => {
          e.stopPropagation();
          setIsVisible((prev) => !prev);
        }}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className={`inline-flex items-center justify-center text-slate-400 hover:text-blue-600 focus:text-blue-600 focus:outline-none transition-colors rounded p-0.5 ${triggerClassName}`}
      >
        {children ? (
          children
        ) : (
          <IconComponent className={`${sizeClasses} shrink-0`} />
        )}
      </button>

      {/* Popover Card */}
      {isVisible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={`absolute z-50 ${positionClasses} w-64 sm:w-72 p-3 bg-slate-900/95 backdrop-blur-md text-white text-xs rounded-xl shadow-2xl border border-slate-700/80 pointer-events-auto transition-all animate-in fade-in duration-150`}
        >
          {title && (
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-700/60">
              <span className="font-bold text-slate-100 text-[11px] tracking-tight flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                {title}
              </span>
            </div>
          )}

          <p className="text-slate-300 leading-relaxed text-[11px]">
            {content}
          </p>

          {formula && (
            <div className="mt-2 p-1.5 bg-slate-800/90 rounded border border-slate-700 text-[10px] font-mono text-amber-300 leading-tight">
              <strong className="text-slate-400">Rule/Criteria:</strong> {formula}
            </div>
          )}

          {note && (
            <p className="mt-1.5 text-[10px] text-slate-400 italic leading-snug">
              {note}
            </p>
          )}

          {/* Micro arrow indicator */}
          <div
            className={`absolute w-2 h-2 bg-slate-900/95 border border-slate-700 rotate-45 ${
              side === 'bottom'
                ? '-top-1 left-1/2 -translate-x-1/2 border-b-0 border-r-0'
                : side === 'left'
                ? '-right-1 top-1/2 -translate-y-1/2 border-b-0 border-l-0'
                : side === 'right'
                ? '-left-1 top-1/2 -translate-y-1/2 border-t-0 border-r-0'
                : '-bottom-1 left-1/2 -translate-x-1/2 border-t-0 border-l-0'
            }`}
          />
        </div>
      )}
    </div>
  );
};
