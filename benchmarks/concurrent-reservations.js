import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const vuCount = Number(__ENV.BOOKING_VUS || 20);
const accepted = new Counter('booking_accepted');
const rejected = new Counter('booking_conflict');

export const options = {
  scenarios: {
    collision: { executor: 'per-vu-iterations', vus: vuCount, iterations: 1, maxDuration: '30s' },
  },
  thresholds: {
    booking_accepted: ['count==1'],
    booking_conflict: [`count==${vuCount - 1}`],
    checks: ['rate==1'],
  },
};

function origin() {
  return __ENV.BOOKING_BASE_URL || 'http://127.0.0.1:5173';
}

export function setup() {
  const email = __ENV.BOOKING_CUSTOMER_EMAIL;
  const password = __ENV.BOOKING_CUSTOMER_PASSWORD;
  if (!email || !password) throw new Error('Set the local seeded customer credentials.');
  const login = http.post(`${origin()}/api/v1/auth/login`, JSON.stringify({ email, password }), {
    headers: { 'Content-Type': 'application/json' },
  });
  if (login.status !== 200) throw new Error(`Demo login returned ${login.status}`);
  const start = new Date(Date.now() + 3 * 86_400_000);
  start.setUTCHours(10, 0, 0, 0);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  return {
    token: login.json('access_token'),
    start_at: __ENV.BOOKING_START || start.toISOString(),
    end_at: __ENV.BOOKING_END || end.toISOString(),
  };
}

export default function (data) {
  const response = http.post(`${origin()}/api/v1/reservations`, JSON.stringify({
    vehicle_id: 1, charger_id: 1, start_at: data.start_at, end_at: data.end_at,
  }), {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${data.token}` },
    responseCallback: http.expectedStatuses(201, 409),
  });
  accepted.add(response.status === 201 ? 1 : 0);
  rejected.add(response.status === 409 ? 1 : 0);
  check(response, { 'response confirms or rejects the slot conflict': r => r.status === 201 || r.status === 409 });
}
