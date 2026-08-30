import React, { useState } from 'react';
import { RefreshCw, PlayCircle, CheckCircle2, Clock, AlertCircle, Settings2, Info } from 'lucide-react';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

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

const STATUS_COLORS: Record<string, string> = {
  idle: '#6b7280',
  QUEUED: '#60a5fa',
  RUNNING: '#f59e0b',
  COMPLETE: '#22c55e',
  PARTIAL_FAILURE: '#f97316',
  ERROR: '#ef4444',
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  QUEUED: <Clock size={16} />,
  RUNNING: <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />,
  COMPLETE: <CheckCircle2 size={16} />,
  PARTIAL_FAILURE: <AlertCircle size={16} />,
  ERROR: <AlertCircle size={16} />,
};

export const PipelineRecomputePage: React.FC = () => {
  const [selectedSteps, setSelectedSteps] = useState<string[]>(['priority']);
  const [operatorNote, setOperatorNote] = useState('');
  const [job, setJob] = useState<Job | null>(null);
  const [polling, setPolling] = useState(false);

  const availableSteps = [
    { id: 'priority', label: 'Village Priority Classification', desc: 'Steps 10B + 10C — re-runs tier assignment with current YAML thresholds (~30s)' },
    { id: 'capacity', label: 'Candidate Area Capacity Enrichment', desc: 'Step 10D — re-runs capacity estimation with current capacity.yaml settings (~10s)' },
  ];

  const toggleStep = (step: string) => {
    setSelectedSteps(prev =>
      prev.includes(step) ? prev.filter(s => s !== step) : [...prev, step]
    );
  };

  const triggerRecompute = async () => {
    if (selectedSteps.length === 0) return;

    const res = await fetch(`${API_BASE}/api/pipeline/recompute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps: selectedSteps, operator_note: operatorNote || undefined }),
    });
    const data = await res.json();
    setJob(data);
    setPolling(true);

    // Poll every 3 seconds until done
    const interval = setInterval(async () => {
      const pollRes = await fetch(`${API_BASE}/api/pipeline/status/${data.job_id}`);
      const pollData = await pollRes.json();
      setJob(pollData);
      if (['COMPLETE', 'PARTIAL_FAILURE', 'ERROR'].includes(pollData.status)) {
        clearInterval(interval);
        setPolling(false);
      }
    }, 3000);
  };

  const jobStatus = job?.status ?? 'idle';
  const statusColor = STATUS_COLORS[jobStatus] ?? '#6b7280';

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <RefreshCw size={26} color="var(--accent-primary)" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Pipeline Recompute
          </h1>
          <span style={{
            background: 'rgba(99,102,241,0.15)', color: '#818cf8',
            borderRadius: '20px', padding: '3px 12px', fontSize: '0.75rem', fontWeight: 600,
          }}>
            Operator-Triggered Workflow
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
          Demonstrates dynamic update capability. Run after changing thresholds in
          {' '}<code style={{ background: 'var(--bg-card)', borderRadius: '4px', padding: '1px 5px', fontSize: '0.85rem' }}>
            configs/priority_thresholds.yaml
          </code>{' '}
          to see updated classification results.
        </p>
      </div>

      {/* Architecture note */}
      <div style={{
        background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)',
        borderRadius: '10px', padding: '14px 18px', marginBottom: '24px',
        display: 'flex', gap: '12px', alignItems: 'flex-start',
      }}>
        <Info size={18} color="#818cf8" style={{ flexShrink: 0, marginTop: '1px' }} />
        <div style={{ color: '#c7d2fe', fontSize: '0.84rem', lineHeight: 1.6 }}>
          <strong>Operator-Triggered Recompute Architecture</strong> — This demonstrates the
          "dynamically identify and update" requirement from SIH26191. When new data or threshold
          changes are applied, an authorized operator triggers recomputation of the classification
          pipeline. Results are updated in the data store after recompute and backend restart.
          This is a prototype demonstration — production deployment would implement automated triggers.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Step Selection */}
        <div>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
            borderRadius: '12px', padding: '20px',
          }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Settings2 size={18} color="var(--accent-primary)" /> Select Steps to Recompute
            </h3>

            {availableSteps.map(step => (
              <label key={step.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: '12px',
                padding: '14px', borderRadius: '8px', cursor: 'pointer',
                background: selectedSteps.includes(step.id) ? 'rgba(99,102,241,0.1)' : 'transparent',
                border: `1px solid ${selectedSteps.includes(step.id) ? 'rgba(99,102,241,0.4)' : 'var(--border-subtle)'}`,
                marginBottom: '10px', transition: 'all 0.15s',
              }}>
                <input
                  type="checkbox"
                  checked={selectedSteps.includes(step.id)}
                  onChange={() => toggleStep(step.id)}
                  style={{ marginTop: '2px', accentColor: 'var(--accent-primary)', width: '16px', height: '16px' }}
                />
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>{step.label}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '3px' }}>{step.desc}</div>
                </div>
              </label>
            ))}

            <div style={{ marginTop: '16px' }}>
              <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: '6px' }}>
                Operator Note (optional)
              </label>
              <input
                value={operatorNote}
                onChange={e => setOperatorNote(e.target.value)}
                placeholder="e.g. Tier 1 threshold updated from 500m to 750m"
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: '8px',
                  background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)', fontSize: '0.85rem', boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              id="btn-trigger-pipeline-recompute"
              onClick={triggerRecompute}
              disabled={selectedSteps.length === 0 || polling}
              style={{
                width: '100%', marginTop: '16px',
                padding: '12px', borderRadius: '8px', border: 'none',
                background: selectedSteps.length > 0 && !polling ? 'var(--accent-primary)' : '#374151',
                color: '#fff', fontSize: '0.95rem', fontWeight: 700,
                cursor: selectedSteps.length > 0 && !polling ? 'pointer' : 'not-allowed',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.2s',
              }}
            >
              {polling ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Running...</>
                : <><PlayCircle size={16} /> Trigger Recompute</>}
            </button>
          </div>
        </div>

        {/* Job Status */}
        <div>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
            borderRadius: '12px', padding: '20px', minHeight: '300px',
          }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Job Status
            </h3>

            {!job ? (
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', padding: '20px 0' }}>
                No job running. Select steps and click "Trigger Recompute" to begin.
              </div>
            ) : (
              <div>
                {/* Status Badge */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  background: `${statusColor}18`, border: `1px solid ${statusColor}44`,
                  borderRadius: '8px', padding: '12px 16px', marginBottom: '16px',
                }}>
                  <span style={{ color: statusColor }}>{STATUS_ICONS[jobStatus]}</span>
                  <div>
                    <div style={{ color: statusColor, fontWeight: 700, fontSize: '0.95rem' }}>
                      {jobStatus}
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                      Job ID: {job.job_id} | Est. {job.estimated_seconds}s
                    </div>
                  </div>
                </div>

                {/* Step Results */}
                {(job.step_results ?? []).map((s, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px', borderRadius: '6px',
                    background: 'var(--bg-secondary)', marginBottom: '8px',
                  }}>
                    <span style={{
                      color: s.status === 'COMPLETE' ? '#22c55e' : s.status === 'FAILED' ? '#ef4444' : '#f59e0b',
                    }}>
                      {s.status === 'COMPLETE' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: 'var(--text-primary)', fontSize: '0.85rem', fontWeight: 600 }}>
                        {s.label ?? s.step}
                      </div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                        {s.status} {s.elapsed_seconds != null ? `— ${s.elapsed_seconds}s` : ''}
                      </div>
                    </div>
                  </div>
                ))}

                {job.status === 'COMPLETE' && (
                  <div style={{
                    marginTop: '12px', padding: '12px',
                    background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)',
                    borderRadius: '8px', color: '#86efac', fontSize: '0.82rem', lineHeight: 1.5,
                  }}>
                    <strong>Complete.</strong> {job.note}
                  </div>
                )}

                {operatorNote && (
                  <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    Operator note: <em>{operatorNote}</em>
                  </div>
                )}

                {job.disclaimer && (
                  <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.75rem', lineHeight: 1.5, opacity: 0.7 }}>
                    {job.disclaimer}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
