import { Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate, useRouter } from '../router';

const links = [
  ['/stations', 'Stations'], ['/chargers', 'Chargers'],
  ['/pricing/calculator', 'Pricing'], ['/tariffs', 'Tariffs'],
  ['/reservations', 'Reservations'], ['/sessions', 'Sessions'],
  ['/invoices', 'Invoices'], ['/maintenance', 'Maintenance'],
  ['/vehicles', 'Vehicles'],
];

export function Navbar() {
  const { user, logout } = useAuth();
  const { path } = useRouter();
  const navigate = useNavigate();
  if (!user) return null;

  const dashboard = '/' + user.role.toLowerCase();

  return (
    <header className="app-header">
      <div className="app-header-top">
        <Link to={dashboard} className="app-brand">
          <Zap size={19} aria-hidden="true" /> GreenCharge
        </Link>
        <div className="app-account">
          <Link to="/profile">{user.full_name}</Link>
          <button type="button" onClick={async () => {
            await logout();
            navigate('/login');
          }}>Sign out</button>
        </div>
      </div>
      <nav className="app-nav" aria-label="Main navigation">
        {[[dashboard, 'Dashboard'], ...links].map(([url, label]) => {
          const active = path === url || (url !== dashboard && path.startsWith(url + '/'));
          return <Link key={url} to={url} aria-current={active ? 'page' : undefined}>{label}</Link>;
        })}
      </nav>
    </header>
  );
}
