import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BrowserRouter, useRouter } from './router';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CustomerDashboard } from './pages/CustomerDashboard';
import { OperatorDashboard } from './pages/OperatorDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { ProfilePage } from './pages/ProfilePage';
import { VehiclesPage } from './pages/VehiclesPage';
import { AddVehiclePage } from './pages/AddVehiclePage';
import { EditVehiclePage } from './pages/EditVehiclePage';
import { VehicleDetailsPage } from './pages/VehicleDetailsPage';
import { StationsPage } from './pages/StationsPage';
import { StationDetailsPage } from './pages/StationDetailsPage';
import { AddStationPage } from './pages/AddStationPage';
import { EditStationPage } from './pages/EditStationPage';
import { ChargersPage } from './pages/ChargersPage';
import { AddChargerPage } from './pages/AddChargerPage';
import { PricingCalculatorPage } from './pages/PricingCalculatorPage';
import { TariffManagementPage } from './pages/TariffManagementPage';
import { AddTariffPage } from './pages/AddTariffPage';
import { PricingRulesPage } from './pages/PricingRulesPage';
import { AddPricingRulePage } from './pages/AddPricingRulePage';
import { ReservationPage } from './pages/ReservationPage';
import { ReservationHistory } from './pages/ReservationHistory';
import { ReservationDetails } from './pages/ReservationDetails';
import { ChargingSessionPage } from './pages/ChargingSessionPage';
import { StartSessionPage } from './pages/StartSessionPage';
import { ActiveSessionsPage } from './pages/ActiveSessionsPage';
import { SessionDetailsPage } from './pages/SessionDetailsPage';
import { SessionHistoryPage } from './pages/SessionHistoryPage';
import { InvoicesPage } from './pages/InvoicesPage';
import { InvoiceDetailsPage } from './pages/InvoiceDetailsPage';
import { PaymentPage } from './pages/PaymentPage';
import { RevenueReportsPage } from './pages/RevenueReportsPage';
import { MaintenanceDashboard } from './pages/MaintenanceDashboard';
import { MaintenanceRequestsPage } from './pages/MaintenanceRequestsPage';
import { CreateMaintenancePage } from './pages/CreateMaintenancePage';
import { MaintenanceDetailsPage } from './pages/MaintenanceDetailsPage';
import { MaintenanceAnalytics } from './pages/MaintenanceAnalytics';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';

const AppRoutes: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { path } = useRouter();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#151b24', color: '#79b9ad', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem', animation: 'pulse 1.5s infinite' }}>⚡</div>
          <p style={{ fontWeight: 600 }}>Connecting to EV Charging Network...</p>
        </div>
      </div>
    );
  }

  // Public Routes
  if (path === '/login') {
    return <LoginPage />;
  }

  if (path === '/register') {
    return <RegisterPage />;
  }

  // Protected Role Routes
  if (path === '/customer') {
    return (
      <ProtectedRoute allowedRoles={['CUSTOMER']}>
        <CustomerDashboard />
      </ProtectedRoute>
    );
  }

  if (path === '/operator') {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <OperatorDashboard />
      </ProtectedRoute>
    );
  }

  if (path === '/admin') {
    return (
      <ProtectedRoute allowedRoles={['ADMIN']}>
        <AdminDashboard />
      </ProtectedRoute>
    );
  }

  if (path === '/profile') {
    return (
      <ProtectedRoute>
        <ProfilePage />
      </ProtectedRoute>
    );
  }

  // Protected Vehicle Routes
  if (path === '/vehicles') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <VehiclesPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/vehicles/add') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <AddVehiclePage />
        </div>
      </ProtectedRoute>
    );
  }

  if (/^\/vehicles\/\d+\/edit$/.test(path)) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <EditVehiclePage />
        </div>
      </ProtectedRoute>
    );
  }

  if (/^\/vehicles\/\d+$/.test(path)) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <VehicleDetailsPage />
        </div>
      </ProtectedRoute>
    );
  }

  // Protected Station & Charger Routes
  if (path === '/stations') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <StationsPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/stations/add') {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <AddStationPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (/^\/stations\/\d+\/chargers\/add$/.test(path)) {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <AddChargerPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (/^\/stations\/\d+\/edit$/.test(path)) {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <EditStationPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (/^\/stations\/\d+$/.test(path)) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <StationDetailsPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/chargers') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ChargersPage />
        </div>
      </ProtectedRoute>
    );
  }

  // Pricing & Tariff Routes
  if (path === '/pricing/calculator' || path === '/pricing') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <PricingCalculatorPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/tariffs') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <TariffManagementPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/tariffs/new') {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <AddTariffPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/pricing-rules') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <PricingRulesPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/pricing-rules/new') {
    return (
      <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <AddPricingRulePage />
        </div>
      </ProtectedRoute>
    );
  }

  // Reservation Management Routes (Module 7)
  if (path === '/reservations') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ReservationHistory />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/reservations/new' || path.startsWith('/reservations/new?')) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ReservationPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/reservations/') && path !== '/reservations/new') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ReservationDetails />
        </div>
      </ProtectedRoute>
    );
  }

  // Charging Session & Energy Metering Routes (Module 8)
  if (path === '/sessions') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ChargingSessionPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/sessions/start' || path.startsWith('/sessions/start?')) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <StartSessionPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/sessions/active') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <ActiveSessionsPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/sessions/history') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <SessionHistoryPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/sessions/') && path !== '/sessions/start' && path !== '/sessions/active' && path !== '/sessions/history') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <SessionDetailsPage />
        </div>
      </ProtectedRoute>
    );
  }

  // Module 9 Invoicing & Payment Routes
  if (path === '/invoices') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <InvoicesPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/invoices/') && path.endsWith('/pay')) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <PaymentPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/invoices/') && !path.endsWith('/pay')) {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <InvoiceDetailsPage />
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/admin/revenue') {
    return (
      <ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }}>
          <Navbar />
          <RevenueReportsPage />
        </div>
      </ProtectedRoute>
    );
  }

  // Module 10 Maintenance & Diagnostics Routes
  if (path === '/maintenance') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
          <Navbar />
          <div className="mx-auto max-w-7xl pt-4">
            <MaintenanceDashboard />
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/maintenance/requests') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
          <Navbar />
          <div className="mx-auto max-w-7xl pt-4">
            <MaintenanceRequestsPage />
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/maintenance/new') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
          <Navbar />
          <div className="mx-auto max-w-7xl pt-4">
            <CreateMaintenancePage />
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (path === '/maintenance/analytics') {
    return (
      <ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']}>
        <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
          <Navbar />
          <div className="mx-auto max-w-7xl pt-4">
            <MaintenanceAnalytics />
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/maintenance/') && path !== '/maintenance/requests' && path !== '/maintenance/new' && path !== '/maintenance/analytics') {
    return (
      <ProtectedRoute>
        <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
          <Navbar />
          <div className="mx-auto max-w-7xl pt-4">
            <MaintenanceDetailsPage />
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  // Default / Root Route: Route based on authentication & role
  if (isAuthenticated && user) {
    if (user.role === 'ADMIN') {
      return (
        <ProtectedRoute allowedRoles={['ADMIN']}>
          <AdminDashboard />
        </ProtectedRoute>
      );
    }
    if (user.role === 'OPERATOR') {
      return (
        <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
          <OperatorDashboard />
        </ProtectedRoute>
      );
    }
    return (
      <ProtectedRoute allowedRoles={['CUSTOMER']}>
        <CustomerDashboard />
      </ProtectedRoute>
    );
  }

  return <LoginPage />;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
