import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } from 'chart.js';
import { apiRequest } from '../../services/api';

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

interface NetworkKpis {
  days: number;
  average_session_minutes: number | null;
  mean_repair_minutes: number | null;
  net_revenue_per_kwh: string | null;
  chargers: {
    charger_id: number;
    charger_code: string;
    station_name: string;
    uptime_percent: number;
    utilization_percent: number;
  }[];
  hours: { hour_utc: number; energy_kwh: string; expected_starts: number }[];
}

export function AnalyticsBarChart({ label, labels, data }: { label: string; labels: string[]; data: number[] }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = new Chart(ref.current, {
      type: 'bar',
      data: { labels, datasets: [{ label, data, backgroundColor: '#79b9ad' }] },
      options: {
        responsive: true,
        scales: { x: { ticks: { color: '#cbd5e1' } }, y: { beginAtZero: true, ticks: { color: '#cbd5e1' } } },
      },
    });
    return () => chart.destroy();
  }, [label, labels, data]);
  return (
    <figure>
      <figcaption>{label}</figcaption>
      <canvas ref={ref} aria-hidden="true" />
      <details>
        <summary>View chart data</summary>
        <table>
          <caption className="sr-only">{label}</caption>
          <tbody>{labels.map((item, i) => <tr key={item}><th scope="row">{item}</th><td>{data[i]}</td></tr>)}</tbody>
        </table>
      </details>
    </figure>
  );
}

export default function NetworkAnalytics({
  userId, revenue,
}: {
  userId: number | undefined;
  revenue: { month: string; amount: string | number }[];
}) {
  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ['network-kpis', userId],
    queryFn: () => apiRequest<NetworkKpis>('/admin/network-kpis'),
  });
  if (isPending) return <p role="status">Loading charger analytics…</p>;
  if (isError || !data) return <p role="alert">Could not load charger analytics. <button onClick={() => void refetch()}>Retry</button></p>;
  if (!data.chargers.length) return <p>No chargers in your managed stations.</p>;

  return (
    <section aria-labelledby="network-kpis" className="network-analytics">
      <h2 id="network-kpis">Charger performance · last {data.days} days</h2>
      <dl>
        <div><dt>Average session</dt><dd>{data.average_session_minutes === null ? '—' : `${data.average_session_minutes} min`}</dd></div>
        <div><dt>Mean time to repair</dt><dd>{data.mean_repair_minutes === null ? '—' : `${data.mean_repair_minutes} min`}</dd></div>
        <div><dt>Collected revenue per kWh</dt><dd>{data.net_revenue_per_kwh === null ? '—' : `₹${data.net_revenue_per_kwh}`}</dd></div>
      </dl>
      <div className="analytics-charts">
        {revenue.length > 0 && (
          <AnalyticsBarChart label="Monthly revenue (INR)"
            labels={revenue.map(month => month.month)}
            data={revenue.map(month => Number(month.amount))} />
        )}
        <AnalyticsBarChart label="Charger utilization (%)"
          labels={data.chargers.map(bay => `${bay.station_name} · ${bay.charger_code}`)}
          data={data.chargers.map(bay => bay.utilization_percent)} />
        <AnalyticsBarChart label="Energy delivered by hour (kWh, UTC)"
          labels={data.hours.map(hour => String(hour.hour_utc).padStart(2, '0') + ':00')}
          data={data.hours.map(hour => Number(hour.energy_kwh))} />
      </div>
      <details>
        <summary>Charger uptime and estimated demand</summary>
        <table>
          <thead><tr><th scope="col">Charger</th><th scope="col">Online time</th></tr></thead>
          <tbody>{data.chargers.map(bay => <tr key={bay.charger_id}><th scope="row">{bay.station_name} · {bay.charger_code}</th><td>{bay.uptime_percent}%</td></tr>)}</tbody>
        </table>
        <table>
          <thead><tr><th scope="col">Hour (UTC)</th><th scope="col">Expected starts per day</th></tr></thead>
          <tbody>{data.hours.map(hour => <tr key={hour.hour_utc}><th scope="row">{hour.hour_utc}:00</th><td>{hour.expected_starts}</td></tr>)}</tbody>
        </table>
      </details>
    </section>
  );
}
