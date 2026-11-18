import React, { useState, useEffect } from 'react';
import { Link } from '../router';
import { pricingService } from '../services/pricing';
import { PricingRule } from '../types/tariff';
import { useAuth } from '../context/AuthContext';

export const PricingRulesPage: React.FC = () => {
  const { user } = useAuth();
  const isPrivileged = user?.role === 'ADMIN' || user?.role === 'OPERATOR';

  const [rules, setRules] = useState<PricingRule[]>([]);
  const [ruleTypeFilter, setRuleTypeFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await pricingService.listPricingRules({
        rule_type: ruleTypeFilter || undefined,
      });
      setRules(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pricing rules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [ruleTypeFilter]);

  const toggleRuleActive = async (rule: PricingRule) => {
    if (!isPrivileged) return;
    try {
      await pricingService.updatePricingRule(rule.rule_id, {
        is_active: !rule.is_active,
      });
      fetchRules();
    } catch (err: any) {
      alert(err.message || 'Failed to update rule');
    }
  };

  const getRuleBadge = (type: string) => {
    switch (type) {
      case 'PEAK_HOUR':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">Peak Hour (Surge)</span>;
      case 'OFF_PEAK':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">Off-Peak (Discount)</span>;
      case 'HIGH_DEMAND':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">High Demand (Surge)</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-800">{type}</span>;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dynamic Pricing Rules</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage peak-hour surge multipliers, off-peak night discounts, and demand-based pricing thresholds.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/tariffs"
            className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 font-semibold text-sm rounded-lg transition"
          >
            ← View Tariffs
          </Link>
          {isPrivileged && (
            <Link
              to="/pricing-rules/new"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-lg shadow transition"
            >
              + Create Rule
            </Link>
          )}
        </div>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6 flex items-center gap-4">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
          Filter Rule Type:
        </label>
        <select
          value={ruleTypeFilter}
          onChange={(e) => setRuleTypeFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none min-w-[200px]"
        >
          <option value="">All Rule Types</option>
          <option value="PEAK_HOUR">Peak Hour</option>
          <option value="OFF_PEAK">Off-Peak</option>
          <option value="HIGH_DEMAND">High Demand</option>
        </select>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-2"></div>
          <p className="text-gray-500 text-sm">Loading dynamic rules...</p>
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-12 text-center border border-dashed border-gray-300 text-gray-500">
          <span className="text-3xl block mb-2">⚡</span>
          <h3 className="font-semibold text-gray-800">No Pricing Rules Found</h3>
          <p className="text-sm mt-1">Configure peak hours or demand triggers to optimize charging utilization.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Rule Type</th>
                <th className="px-6 py-3.5">Tariff Ref</th>
                <th className="px-6 py-3.5">Condition / Window</th>
                <th className="px-6 py-3.5">Multiplier</th>
                <th className="px-6 py-3.5">Priority</th>
                <th className="px-6 py-3.5">Status</th>
                {isPrivileged && <th className="px-6 py-3.5 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 text-sm">
              {rules.map((r) => (
                <tr key={r.rule_id} className="hover:bg-gray-50 transition">
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getRuleBadge(r.rule_type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-700">
                    Tariff #{r.tariff_id}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {r.rule_type === 'HIGH_DEMAND' ? (
                      <span className="font-medium text-gray-900">
                        Station Demand &gt;= {Number(r.demand_threshold_percent).toFixed(0)}%
                      </span>
                    ) : (
                      <span>
                        {r.start_time} to {r.end_time}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-extrabold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                      {Number(r.price_multiplier).toFixed(3)}x
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-800">
                    Level {r.priority}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      r.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {r.is_active ? '● Active' : '○ Inactive'}
                    </span>
                  </td>
                  {isPrivileged && (
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => toggleRuleActive(r)}
                        className={`text-xs font-semibold px-3 py-1 rounded transition ${
                          r.is_active
                            ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                        }`}
                      >
                        {r.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
