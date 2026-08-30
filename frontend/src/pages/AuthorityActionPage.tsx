import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldAlert, Download, AlertTriangle, Users, Building2,
  MapPin, ChevronRight, AlertCircle, Printer, Filter,
  CheckCircle2, Clock, Eye, RefreshCw
} from 'lucide-react';
import { apiClient } from '../api/client';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const DISCLAIMER =
  'DECISION SUPPORT ONLY — NOT AN OFFICIAL RELOCATION ORDER, EVACUATION NOTICE, OR GOVERNMENT DECLARATION. ' +
  'All classifications are based on preliminary GIS screening. ' +
  'Field verification, geotechnical assessment, and official SDMA/DDMA authorization are required before any administrative action.';

const TIER_COLORS: Record<string, string> = {
  Tier1_AttentionPriority: '#ef4444',
  Tier2_ElevatedAttention: '#f97316',
  Tier3_Monitoring: '#eab308',
  BeyondProximity: '#6b7280',
};

const TIER_LABELS: Record<string, string> = {
  Tier1_AttentionPriority: 'Tier 1 — Immediate Field Assessment',
  Tier2_ElevatedAttention: 'Tier 2 — Short-Term Planning Review',
};

function fetchActionQueue(highVulnOnly: boolean, tiers: string) {
  return fetch(
    `${API_BASE}/api/authority/action-queue?tiers=${encodeURIComponent(tiers)}&high_vuln_only=${highVulnOnly}&limit=200`
  ).then(r => r.json());
}

function fetchBlockSummary() {
  return fetch(`${API_BASE}/api/authority/block-summary`).then(r => r.json());
}

function downloadCSV(tiers: string) {
  window.open(
    `${API_BASE}/api/authority/report.csv?tiers=${encodeURIComponent(tiers)}`,
    '_blank'
  );
}

export const AuthorityActionPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'blocks'>('queue');
  const [showTier2, setShowTier2] = useState(true);
  const [highVulnOnly, setHighVulnOnly] = useState(false);

  const tiers = showTier2
    ? 'Tier1_AttentionPriority,Tier2_ElevatedAttention'
    : 'Tier1_AttentionPriority';

  const { data: queueData, isLoading: queueLoading } = useQuery({
    queryKey: ['authority-queue', tiers, highVulnOnly],
    queryFn: () => fetchActionQueue(highVulnOnly, tiers),
  });

  const { data: blockData, isLoading: blockLoading } = useQuery({
    queryKey: ['authority-blocks'],
    queryFn: fetchBlockSummary,
  });

  const queue = queueData?.action_queue ?? [];
  const summary = queueData?.action_queue_summary ?? {};

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <ShieldAlert size={28} color="#ef4444" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Authority Action Center
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.95rem' }}>
          Priority decision-support report for SDMA/DDMA. District: Rudraprayag, Uttarakhand.
        </p>
      </div>

      {/* Disclaimer Banner */}
      <div style={{
        background: 'rgba(239,68,68,0.08)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: '10px',
        padding: '14px 18px',
        marginBottom: '24px',
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
      }}>
        <AlertTriangle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: '1px' }} />
        <p style={{ margin: 0, color: '#fca5a5', fontSize: '0.82rem', lineHeight: 1.5 }}>
          {DISCLAIMER}
        </p>
      </div>

      {/* Summary Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px', marginBottom: '24px' }}>
        {[
          { label: 'Villages Screened', value: queueData?.total_villages_screened ?? 653, icon: <Building2 size={20} />, color: '#60a5fa' },
          { label: 'Tier 1 Villages', value: summary?.tier_counts?.Tier1_AttentionPriority ?? 12, icon: <AlertTriangle size={20} />, color: '#ef4444' },
          { label: 'Tier 2 Villages', value: summary?.tier_counts?.Tier2_ElevatedAttention ?? 69, icon: <AlertCircle size={20} />, color: '#f97316' },
          { label: 'At-Risk Population (T1+T2)', value: (summary?.total_at_risk_population ?? 27762)?.toLocaleString(), icon: <Users size={20} />, color: '#a78bfa' },
        ].map((stat, i) => (
          <div key={i} style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: stat.color }}>
              {stat.icon}
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{stat.label}</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        marginBottom: '20px', flexWrap: 'wrap',
      }}>
        {/* Tabs */}
        <div style={{ display: 'flex', background: 'var(--bg-card)', borderRadius: '8px', padding: '4px' }}>
          {[['queue', 'Action Queue'], ['blocks', 'Block Summary']].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setActiveTab(k as 'queue' | 'blocks')}
              style={{
                padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                background: activeTab === k ? 'var(--accent-primary)' : 'transparent',
                color: activeTab === k ? '#fff' : 'var(--text-secondary)',
                fontSize: '0.88rem', fontWeight: activeTab === k ? 600 : 400,
                transition: 'all 0.15s',
              }}
            >{label}</button>
          ))}
        </div>

        {activeTab === 'queue' && (
          <>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={showTier2} onChange={e => setShowTier2(e.target.checked)} />
              Include Tier 2
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={highVulnOnly} onChange={e => setHighVulnOnly(e.target.checked)} />
              High vulnerability only (≥2 flags)
            </label>
          </>
        )}

        {/* Export buttons */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          <button
            id="btn-print-authority-report"
            onClick={() => window.print()}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 14px', borderRadius: '8px',
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.85rem',
            }}
          >
            <Printer size={15} /> Print
          </button>
          <button
            id="btn-download-priority-csv"
            onClick={() => downloadCSV(tiers)}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 14px', borderRadius: '8px',
              background: 'var(--accent-primary)', border: 'none',
              color: '#fff', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
            }}
          >
            <Download size={15} /> Download CSV
          </button>
        </div>
      </div>

      {/* Action Queue */}
      {activeTab === 'queue' && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Priority Action Queue
            </h3>
            <span style={{
              background: 'rgba(239,68,68,0.15)', color: '#ef4444',
              borderRadius: '20px', padding: '2px 10px', fontSize: '0.78rem', fontWeight: 600,
            }}>
              {queue.length} villages
            </span>
            <span style={{ marginLeft: '8px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
              Sorted by proximity to hazard zone (closest first)
            </span>
          </div>

          {queueLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite' }} />
              <p>Loading action queue...</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    {['Village', 'Priority', 'Distance to Red Zone', 'Population', 'HH', 'Vulnerability', 'Recommended Action'].map(h => (
                      <th key={h} style={{
                        padding: '10px 14px', textAlign: 'left',
                        color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.78rem',
                        borderBottom: '1px solid var(--border-subtle)', whiteSpace: 'nowrap',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queue.map((v: any, i: number) => (
                    <tr key={v.village_id ?? i} style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                    }}>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>
                        {v.village_name ?? 'Unknown'}
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>ID: {v.village_id}</div>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{
                          background: `${TIER_COLORS[v.priority_tier]}22`,
                          color: TIER_COLORS[v.priority_tier],
                          borderRadius: '6px', padding: '3px 8px', fontSize: '0.75rem', fontWeight: 700,
                          whiteSpace: 'nowrap',
                        }}>
                          {v.relocation_horizon_display ?? v.priority_tier}
                        </span>
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                        {v.nearest_hazard_distance_m != null
                          ? `${Math.round(v.nearest_hazard_distance_m).toLocaleString()} m`
                          : '—'}
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)' }}>
                        {v.tot_pop?.toLocaleString() ?? '—'}
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)' }}>
                        {v.households?.toLocaleString() ?? '—'}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                          <span style={{
                            color: v.vulnerability_flag_count >= 2 ? '#f97316' : 'var(--text-secondary)',
                            fontSize: '0.78rem', fontWeight: v.vulnerability_flag_count >= 2 ? 600 : 400,
                          }}>
                            {v.vulnerability_context ?? '—'}
                          </span>
                          {v.active_vulnerability_flags?.length > 0 && (
                            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                              {v.active_vulnerability_flags.slice(0, 2).map((f: string) => (
                                <span key={f} style={{
                                  background: 'rgba(249,115,22,0.15)', color: '#f97316',
                                  borderRadius: '4px', padding: '1px 5px', fontSize: '0.68rem',
                                }}>{f}</span>
                              ))}
                              {v.active_vulnerability_flags.length > 2 && (
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.68rem' }}>
                                  +{v.active_vulnerability_flags.length - 2}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', fontSize: '0.8rem', maxWidth: '260px' }}>
                        {v.recommended_action ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {queue.length === 0 && !queueLoading && (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No villages match the selected filter criteria.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Block Summary */}
      {activeTab === 'blocks' && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Sub-District / Block Summary
            </h3>
            <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
              Aggregated by administrative sub-district. Sorted by Tier 1 + Tier 2 village count.
            </p>
          </div>

          {blockLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading...</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    {['Sub-District ID', 'Total Villages', 'Tier 1 (Immediate)', 'Tier 2 (Short-Term)', 'Tier 3 (Monitor)', 'At-Risk Pop (T1+T2)', 'High-Vuln Villages'].map(h => (
                      <th key={h} style={{
                        padding: '10px 14px', textAlign: 'left',
                        color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.78rem',
                        borderBottom: '1px solid var(--border-subtle)', whiteSpace: 'nowrap',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(blockData?.block_summary ?? []).map((b: any, i: number) => (
                    <tr key={b.subdist_id ?? i} style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                    }}>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>{b.subdist_id}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>{b.total_villages}</td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{ color: '#ef4444', fontWeight: 700, fontSize: '1rem' }}>{b.tier1_immediate}</span>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{ color: '#f97316', fontWeight: 700 }}>{b.tier2_short_term}</span>
                      </td>
                      <td style={{ padding: '10px 14px', color: '#eab308' }}>{b.tier3_monitoring}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)' }}>{b.at_risk_population_tier1_2?.toLocaleString()}</td>
                      <td style={{ padding: '10px 14px', color: b.high_vulnerability_villages > 0 ? '#f97316' : 'var(--text-secondary)' }}>
                        {b.high_vulnerability_villages}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!blockData?.block_summary || blockData.block_summary.length === 0) && (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  {blockData?.status === 'BLOCK_ID_UNAVAILABLE'
                    ? 'Sub-district aggregation unavailable — shrug_subdist_id field not present in data.'
                    : 'No block data available.'}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Methodology Note */}
      <div style={{
        marginTop: '24px', padding: '14px 18px',
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        borderRadius: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--text-primary)' }}>Classification Methodology:</strong>{' '}
        Rule-based GIS proximity analysis using Copernicus GLO-30 DEM terrain screening and Census 2011 PCA data.
        Tier 1: within 500m of Candidate Red Zone + MH Class ≥ 2. Tier 2: within 2,000m.
        Vulnerability flags are Census 2011 upper tertile thresholds (district P75 values).
        Relocation horizon labels are planning categories, NOT official orders.
      </div>
    </div>
  );
};
