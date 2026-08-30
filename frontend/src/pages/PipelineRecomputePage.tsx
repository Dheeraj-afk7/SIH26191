import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  RefreshCw,
  PlayCircle,
  CheckCircle2,
  Clock,
  AlertCircle,
  Settings2,
  Info,
  Building2,
  Landmark,
  Layers,
  ArrowRight,
  Sparkles,
  Terminal
} from 'lucide-react';
import { InfoTooltip } from '../components/shared/InfoTooltip';
import { API_BASE_URL } from '../config/api';

type JobStatus = 'idle' | 'QUEUED' | 'RUNNING' | 'COMPLETE' | 'PARTIAL_FAILURE' | 'ERROR';

interface Job {
  job_id: string;
  status: JobStatus;
  steps: string[];
  estimated_seconds: number;
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
  step_results?: Array<{
    step: string;
    label: string;
    status: string;
    elapsed_seconds?: number;
  }>;
  note?: string;
  disclaimer?: string;
}

export const PipelineRecomputePage: React.FC = () => {
  const [selectedSteps, setSelectedSteps] = useState<string[]>(['priority']);
  const [operatorNote, setOperatorNote] = useState('');
  const [job, setJob] = useState<Job | null>(null);
  const [polling, setPolling] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const availableSteps = [
    {
      id: 'priority',
      title: 'Village Priority Classification',
      stepNum: 'Steps 10B + 10C',
      estimated: '~5s',
      desc: 'Re-samples multi-hazard raster scores at centroids, recalculates planar distances to 289 red zones, and deterministically assigns Tier 1, Tier 2, and Tier 3 priority profiles.',
      icon: Building2,
    },
    {
      id: 'capacity',
      title: 'Candidate Area Capacity Enrichment',
      stepNum: 'Step 10D',
      estimated: '~5s',
      desc: 'Re-evaluates 2,998 terrain polygons against slope thresholds (≤ 20°), road proximity, and hazard buffer zones to calculate safe population capacity.',
      icon: Layers,
    },
    {
      id: 'infrastructure',
      title: 'Critical Infrastructure & Routing',
      stepNum: 'Phase 4 Ingestion',
      estimated: '~10s',
      desc: 'Ingests 291 critical facilities (Hospitals, CHCs, PHCs, Schools, Emergency) and recomputes road network shortest paths and travel times.',
      icon: Landmark,
    },
    {
      id: 'decision_summary',
      title: 'Decision Summary & Metadata',
      stepNum: 'Step 10E Synthesis',
      estimated: '~3s',
      desc: 'Regenerates decision_summary.json, decision_metadata.json, and the comprehensive decision support markdown report.',
      icon: Terminal,
    },
  ];

  // Timer while running
  useEffect(() => {
    let timer: any;
    if (polling) {
      timer = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(timer);
  }, [polling]);

  const toggleStep = (step: string) => {
    setSelectedSteps(prev =>
      prev.includes(step) ? prev.filter(s => s !== step) : [...prev, step]
    );
  };

  const triggerRecompute = async () => {
    if (selectedSteps.length === 0) return;

    try {
      setPolling(true);
      const res = await fetch(`${API_BASE_URL}/api/pipeline/recompute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps: selectedSteps, operator_note: operatorNote || undefined }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const detail = errJson?.detail || `HTTP ${res.status} ${res.statusText}`;
        throw new Error(detail);
      }
      const data = await res.json();
      setJob(data);

      // Poll every 2 seconds until done
      const interval = setInterval(async () => {
        try {
          const pollRes = await fetch(`${API_BASE_URL}/api/pipeline/status/${data.job_id}`);
          if (!pollRes.ok) return;
          const pollData = await pollRes.json();
          setJob(pollData);
          if (['COMPLETE', 'PARTIAL_FAILURE', 'ERROR'].includes(pollData.status)) {
            clearInterval(interval);
            setPolling(false);
          }
        } catch {
          // Keep polling on transient network error
        }
      }, 2000);
    } catch (err: any) {
      setPolling(false);
      setJob({
        job_id: 'err-' + Date.now(),
        status: 'ERROR',
        steps: selectedSteps,
        estimated_seconds: 0,
        note: err?.message || `Could not connect to backend pipeline API at ${API_BASE_URL}. Ensure FastAPI server is active.`,
      });
    }
  };


  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-600 text-white shadow-sm shrink-0">
              <RefreshCw className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                Pipeline Recompute Engine
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                  Dynamic Updates
                </span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Operator-triggered workflow to recompute classifications after threshold or spatial data changes
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Architecture & Compliance Note */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-lg bg-blue-100 border border-blue-200 text-blue-700 shrink-0 mt-0.5">
            <Info className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-wider text-blue-900 mb-0.5">
              Operator-Triggered Recompute Architecture (SIH26191 Compliance)
            </p>
            <p className="text-xs text-blue-950 leading-relaxed">
              This engine demonstrates the <strong className="text-blue-900 font-semibold">"dynamically identify and update"</strong> requirement.
              When district hazard criteria, slope tolerances, or new spatial layers are modified in YAML configs,
              an authorized operator can trigger recomputation on demand.
              Updated profiles are committed to GeoPackage stores and served in real time to the Decision Support dashboards.
            </p>
          </div>
        </div>
      </div>

      {/* 3. Main Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form Controls (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Select Pipeline Steps to Recompute
                </h3>
              </div>
              <span className="text-xs font-semibold text-slate-400">
                {selectedSteps.length} of {availableSteps.length} selected
              </span>
            </div>

            {/* Step Selection Cards */}
            <div className="space-y-3">
              {availableSteps.map((step) => {
                const isSelected = selectedSteps.includes(step.id);
                const Icon = step.icon;
                return (
                  <div
                    key={step.id}
                    onClick={() => toggleStep(step.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-150 relative ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // handled by parent div
                        className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mt-0.5 cursor-pointer"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                            <span className="text-xs font-bold text-slate-900">
                              {step.title}
                            </span>
                          </div>
                          <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {step.estimated}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
                          {step.stepNum}
                        </p>
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                          {step.desc}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Operator Audit Note */}
            <div className="space-y-1.5 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">
                  Operator Audit Log Note (optional)
                </label>
                <InfoTooltip
                  title="Audit Trail Logging"
                  content="Logged to pipeline metadata to record why this recomputation was triggered (e.g. monsoon review, new contour data, threshold update)."
                  side="top"
                />
              </div>
              <input
                type="text"
                value={operatorNote}
                onChange={(e) => setOperatorNote(e.target.value)}
                placeholder="e.g. Tier 1 hazard threshold updated from 500m to 750m for monsoon review"
                className="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white text-slate-800 placeholder-slate-400 transition-all"
              />
            </div>

            {/* Trigger Button */}
            <button
              id="btn-trigger-pipeline-recompute"
              onClick={triggerRecompute}
              disabled={selectedSteps.length === 0 || polling}
              className={`w-full py-3 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-sm transition-all ${
                selectedSteps.length > 0 && !polling
                  ? 'bg-blue-700 hover:bg-blue-800 text-white shadow-blue-700/20 hover:shadow-md cursor-pointer'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
              }`}
            >
              {polling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Executing Pipeline ({elapsedSeconds}s elapsed)...</span>
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4 text-white" />
                  <span>OPERATOR-TRIGGERED DYNAMIC RECOMPUTATION</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Execution Monitor (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 min-h-[380px] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-slate-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Execution Status & Telemetry
                </h3>
              </div>
              {polling && (
                <span className="flex items-center gap-1.5 text-[11px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  Running
                </span>
              )}
            </div>

            <div className="flex-1 py-4 flex flex-col justify-center">
              {!job ? (
                <div className="text-center py-8 space-y-2">
                  <div className="w-12 h-12 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center mx-auto text-slate-400">
                    <Clock className="w-6 h-6" />
                  </div>
                  <p className="text-xs font-bold text-slate-700">Ready for Execution</p>
                  <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                    Select the target pipeline steps and click "Trigger Pipeline Recompute" to begin automated processing.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Status Banner */}
                  <div
                    className={`p-4 rounded-xl border flex items-center gap-3 ${
                      job.status === 'COMPLETE'
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                        : job.status === 'RUNNING' || job.status === 'QUEUED'
                        ? 'bg-blue-50 border-blue-200 text-blue-900'
                        : 'bg-red-50 border-red-200 text-red-900'
                    }`}
                  >
                    {job.status === 'COMPLETE' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    ) : job.status === 'RUNNING' || job.status === 'QUEUED' ? (
                      <RefreshCw className="w-5 h-5 text-blue-600 animate-spin shrink-0" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold uppercase tracking-wider">
                        {job.status}
                      </p>
                      <p className="text-[11px] opacity-80 font-mono mt-0.5 truncate">
                        Job: {job.job_id}
                      </p>
                    </div>
                  </div>

                  {/* Step Breakdown */}
                  {job.step_results && job.step_results.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Step Execution Results
                      </p>
                      <div className="space-y-1.5">
                        {job.step_results.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                          >
                            <div className="flex items-center gap-2">
                              {step.status === 'COMPLETE' ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                              ) : (
                                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                              )}
                              <span className="font-semibold text-slate-800">
                                {step.label || step.step}
                              </span>
                            </div>
                            <span className="font-mono text-[11px] font-bold text-slate-500">
                              {step.elapsed_seconds != null ? `${step.elapsed_seconds}s` : step.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Success Notes & Links */}
                  {job.status === 'COMPLETE' && (
                    <div className="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-200 space-y-2.5 text-xs text-emerald-900">
                      <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                        <Sparkles className="w-4 h-4 text-emerald-600" />
                        <span>Recompute Complete</span>
                      </div>
                      <p className="text-[11px] leading-relaxed text-emerald-800">
                        {job.note || 'Classification outputs refreshed in GeoPackage and live API.'}
                      </p>
                      <div className="pt-1 flex gap-2">
                        <Link
                          to="/authority"
                          className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-700 hover:text-blue-900 underline"
                        >
                          View Authority Action Center
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  )}

                  {/* Error & Failure Notice */}
                  {(job.status === 'ERROR' || job.status === 'PARTIAL_FAILURE') && (
                    <div className="p-3.5 rounded-xl bg-red-50/90 border border-red-200 space-y-2.5 text-xs text-red-900">
                      <div className="flex items-center gap-1.5 font-bold text-red-800">
                        <AlertCircle className="w-4 h-4 text-red-600" />
                        <span>Execution Notice</span>
                      </div>
                      <p className="text-[11px] leading-relaxed text-red-800">
                        {job.note || 'Pipeline recomputation encountered an error.'}
                      </p>
                      <div className="pt-1">
                        <button
                          onClick={triggerRecompute}
                          disabled={polling}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-700 hover:bg-red-800 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          Retry Recomputation
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Quick Reference Box */}
            <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400 space-y-1">
              <p className="font-semibold text-slate-500">Active Rule Thresholds:</p>
              <div className="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[10px] text-slate-600">
                <span>Tier 1: ≤ 500m + MH ≥ 2</span>
                <span>•</span>
                <span>Tier 2: ≤ 2,000m</span>
                <span>•</span>
                <span>Slope: ≤ 20°</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
