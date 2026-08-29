import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useDecisionSummary } from '../../hooks';
import { PRIORITY_TIERS, PriorityTierKey } from '../../config/constants';
import { formatNumber } from '../../utils/formatters';

export const TierDistributionChart: React.FC = () => {
  const { data: summary } = useDecisionSummary();

  const tierDist = summary?.village_priority?.tier_distribution;

  const data = (Object.keys(PRIORITY_TIERS) as PriorityTierKey[]).map((key) => {
    const stat = tierDist?.[key];
    const config = PRIORITY_TIERS[key];
    return {
      name: config.shortLabel,
      key,
      count: stat?.count || 0,
      population: stat?.population || 0,
      percentage: stat?.percentage || 0,
      color: config.mapColor,
    };
  });

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm flex flex-col h-[380px]">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Habitation Priority Distribution
          </h3>
          <p className="text-[11px] text-slate-500">
            653 Habitations classified by proximity and multi-hazard class
          </p>
        </div>
      </div>

      <div className="flex-1 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: '#64748B' }} />
            <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11, fill: '#334155', fontWeight: 600 }} />
            <Tooltip
              formatter={(value: any, _name: any, item: any) => [
                `${formatNumber(value)} Habitations (${item.payload.percentage.toFixed(1)}%)`,
                'Count',
              ]}
              labelFormatter={(label) => `Classification: ${label}`}
              contentStyle={{
                backgroundColor: '#0F2044',
                borderColor: '#1E3A8A',
                borderRadius: '8px',
                color: '#FFFFFF',
                fontSize: '12px',
              }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-center">
        {data.map((item) => (
          <div key={item.key} className="text-xs">
            <p className="font-bold text-slate-900 font-mono">{item.count}</p>
            <p className="text-[10px] text-slate-500 truncate">{item.name}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
