import { useQuery } from '@tanstack/react-query';
import { CalendarClock, MapPin, Plug, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { reservationService } from '../services/reservation';
import { sessionService } from '../services/session';
import { vehicleService } from '../services/vehicle';

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });

export function CustomerDashboard() {
  const { user } = useAuth();
  const id = user?.user_id;
  const bookings = useQuery({
    queryKey: ['driver-reservations', id],
    queryFn: () => reservationService.listReservations(),
  });
  const vehicles = useQuery({
    queryKey: ['driver-vehicles', id],
    queryFn: () => vehicleService.listVehicles(),
  });
  const charging = useQuery({
    queryKey: ['driver-sessions', id],
    queryFn: () => sessionService.getActiveSessions(),
  });

  const upcoming = bookings.data?.filter(reservation =>
    ['CONFIRMED', 'PENDING'].includes(reservation.status) && Date.parse(reservation.end_at) > Date.now(),
  ).sort((a, b) => Date.parse(a.start_at) - Date.parse(b.start_at))[0];
  const active = charging.data?.[0];

  return (
    <div className="driver-dashboard">
      <Navbar />
      <main className="driver-content">
        <header>
          <h1>Welcome, {user?.full_name}</h1>
          <div className="driver-actions">
            <Link className="driver-primary" to="/stations"><MapPin size={20} aria-hidden /> Find a charger</Link>
            <Link to="/reservations/new"><CalendarClock size={20} aria-hidden /> Book a slot</Link>
          </div>
        </header>
        <div className="driver-cards">
          <section aria-labelledby="driver-booking">
            <h2 id="driver-booking"><CalendarClock size={18} aria-hidden /> Next reservation</h2>
            {bookings.isPending && <p role="status">Loading reservations…</p>}
            {bookings.isError && <p role="alert">Could not load reservations. <button onClick={() => void bookings.refetch()}>Retry</button></p>}
            {bookings.isSuccess && (upcoming ? (
              <>
                <p>{upcoming.station?.station_name ?? 'Charging station'}</p>
                <p>{dateFormat.format(new Date(upcoming.start_at))}</p>
                <Link to={`/reservations/${upcoming.reservation_id}`}>View booking</Link>
              </>
            ) : <p>No upcoming reservations.</p>)}
          </section>
          <section aria-labelledby="driver-session">
            <h2 id="driver-session"><Zap size={18} aria-hidden /> Charging session</h2>
            {charging.isPending && <p role="status">Loading sessions…</p>}
            {charging.isError && <p role="alert">Could not load charging sessions. <button onClick={() => void charging.refetch()}>Retry</button></p>}
            {charging.isSuccess && (active ? (
              <>
                <p>Charging at {active.station?.station_name ?? 'your station'}</p>
                <Link to={`/sessions/${active.session_id}`}>View session</Link>
              </>
            ) : <p>No active charging session.</p>)}
          </section>
          <section aria-labelledby="driver-vehicles">
            <h2 id="driver-vehicles"><Plug size={18} aria-hidden /> Your vehicles</h2>
            {vehicles.isPending && <p role="status">Loading vehicles…</p>}
            {vehicles.isError && <p role="alert">Could not load vehicles. <button onClick={() => void vehicles.refetch()}>Retry</button></p>}
            {vehicles.isSuccess && (vehicles.data.length ? (
              <p>{vehicles.data.length} registered {vehicles.data.length === 1 ? 'vehicle' : 'vehicles'}</p>
            ) : <p>Add your first vehicle to check connector compatibility.</p>)}
            <Link to="/vehicles">Manage vehicles</Link>
          </section>
        </div>
      </main>
    </div>
  );
}
