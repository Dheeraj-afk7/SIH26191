import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
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
  const [coords, setCoords] = useState<{
    top: number;
    left: number;
    transform: string;
    resolvedSide: 'top' | 'bottom' | 'left' | 'right';
  }>({
    top: 0,
    left: 0,
    transform: 'none',
    resolvedSide: 'top',
  });

  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipWidth = 288; // 18rem
    const padding = 12;

    let targetSide = side === 'auto' ? 'top' : side;
    
    // Auto fallback for top if near screen top
    if (targetSide === 'top' && rect.top < 150) {
      targetSide = 'bottom';
    }
    // Auto fallback for bottom if near screen bottom
    if (targetSide === 'bottom' && rect.bottom > window.innerHeight - 150) {
      targetSide = 'top';
    }
    // Auto fallback for right if overflowing viewport
    if (targetSide === 'right' && rect.right + tooltipWidth + padding > window.innerWidth) {
      targetSide = rect.left > tooltipWidth + padding ? 'left' : 'bottom';
    }
    // Auto fallback for left if overflowing viewport
    if (targetSide === 'left' && rect.left - tooltipWidth - padding < 0) {
      targetSide = 'right';
    }

    let top = 0;
    let left = 0;
    let transform = 'none';

    if (targetSide === 'right') {
      top = Math.max(padding, Math.min(window.innerHeight - 100, rect.top + rect.height / 2));
      left = rect.right + 8;
      transform = 'translateY(-50%)';
    } else if (targetSide === 'left') {
      top = Math.max(padding, Math.min(window.innerHeight - 100, rect.top + rect.height / 2));
      left = Math.max(padding, rect.left - 8);
      transform = 'translate(-100%, -50%)';
    } else if (targetSide === 'bottom') {
      top = rect.bottom + 8;
      left = Math.max(padding, Math.min(window.innerWidth - tooltipWidth - padding, rect.left + rect.width / 2 - tooltipWidth / 2));
      transform = 'none';
    } else {
      // top
      top = rect.top - 8;
      left = Math.max(padding, Math.min(window.innerWidth - tooltipWidth - padding, rect.left + rect.width / 2 - tooltipWidth / 2));
      transform = 'translateY(-100%)';
    }

    setCoords({
      top,
      left,
      transform,
      resolvedSide: targetSide as 'top' | 'bottom' | 'left' | 'right',
    });
  }, [side]);

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      const handleScrollOrResize = () => updatePosition();
      window.addEventListener('scroll', handleScrollOrResize, true);
      window.addEventListener('resize', handleScrollOrResize);
      return () => {
        window.removeEventListener('scroll', handleScrollOrResize, true);
        window.removeEventListener('resize', handleScrollOrResize);
      };
    }
  }, [isVisible, updatePosition]);

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

  const IconComponent = icon === 'help' ? HelpCircle : Info;

  return (
    <div
      ref={triggerRef}
      className={`relative inline-flex items-center align-middle ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {/* Trigger Button */}
      <button
        type="button"
        aria-label={title || 'Information'}
        onClick={(e) => {
          e.stopPropagation();
          setIsVisible((prev) => !prev);
        }}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className={`inline-flex items-center justify-center text-slate-400 hover:text-blue-500 focus:text-blue-500 focus:outline-none transition-colors rounded p-0.5 ${triggerClassName}`}
      >
        {children ? (
          children
        ) : (
          <IconComponent className={`${sizeClasses} shrink-0`} />
        )}
      </button>

      {/* Portalled Popover Card */}
      {isVisible &&
        createPortal(
          <div
            ref={tooltipRef}
            role="tooltip"
            style={{
              position: 'fixed',
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              transform: coords.transform,
              zIndex: 99999,
            }}
            className="w-72 max-w-[calc(100vw-24px)] p-3 bg-slate-900/95 backdrop-blur-md text-white text-xs rounded-xl shadow-2xl border border-slate-700/80 pointer-events-auto transition-all animate-in fade-in zoom-in-95 duration-150"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
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
              className={`absolute w-2 h-2 bg-slate-900 border border-slate-700 rotate-45 pointer-events-none ${
                coords.resolvedSide === 'bottom'
                  ? '-top-1 left-4 border-b-0 border-r-0'
                  : coords.resolvedSide === 'left'
                  ? '-right-1 top-1/2 -translate-y-1/2 border-b-0 border-l-0'
                  : coords.resolvedSide === 'right'
                  ? '-left-1 top-1/2 -translate-y-1/2 border-t-0 border-r-0'
                  : '-bottom-1 left-4 border-t-0 border-l-0'
              }`}
            />
          </div>,
          document.body
        )}
    </div>
  );
};
