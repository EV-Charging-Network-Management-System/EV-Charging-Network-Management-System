import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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

  const home = isAuthenticated && user ? '/' + user.role.toLowerCase() : '/login';
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/customer" element={(
          <ProtectedRoute allowedRoles={['CUSTOMER']}>
            <CustomerDashboard />
          </ProtectedRoute>
      )} />
      <Route path="/operator" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <OperatorDashboard />
          </ProtectedRoute>
      )} />
      <Route path="/admin" element={(
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <AdminDashboard />
          </ProtectedRoute>
      )} />
      <Route path="/profile" element={(
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
      )} />
      <Route path="/vehicles" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <VehiclesPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/vehicles/add" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <AddVehiclePage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/vehicles/:id/edit" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <EditVehiclePage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/vehicles/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <VehicleDetailsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/stations" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <StationsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/stations/add" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <AddStationPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/stations/:id/chargers/add" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <AddChargerPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/stations/:id/edit" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <EditStationPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/stations/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <StationDetailsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/chargers" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ChargersPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/pricing/calculator" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <PricingCalculatorPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/pricing" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <PricingCalculatorPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/tariffs" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <TariffManagementPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/tariffs/new" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <AddTariffPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/pricing-rules" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <PricingRulesPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/pricing-rules/new" element={(
          <ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <AddPricingRulePage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/reservations" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ReservationHistory />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/reservations/new" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ReservationPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/reservations/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ReservationDetails />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/sessions" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ChargingSessionPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/sessions/start" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <StartSessionPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/sessions/active" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <ActiveSessionsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/sessions/history" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <SessionHistoryPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/sessions/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <SessionDetailsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/invoices" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <InvoicesPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/invoices/:id/pay" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <PaymentPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/invoices/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <InvoiceDetailsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/admin/revenue" element={(
          <ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }}>
              <Navbar />
              <RevenueReportsPage />
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/maintenance" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
              <Navbar />
              <div className="mx-auto max-w-7xl pt-4">
                <MaintenanceDashboard />
              </div>
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/maintenance/requests" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
              <Navbar />
              <div className="mx-auto max-w-7xl pt-4">
                <MaintenanceRequestsPage />
              </div>
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/maintenance/new" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
              <Navbar />
              <div className="mx-auto max-w-7xl pt-4">
                <CreateMaintenancePage />
              </div>
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/maintenance/analytics" element={(
          <ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']}>
            <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
              <Navbar />
              <div className="mx-auto max-w-7xl pt-4">
                <MaintenanceAnalytics />
              </div>
            </div>
          </ProtectedRoute>
      )} />
      <Route path="/maintenance/:id" element={(
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#151b24' }} className="p-4 sm:p-6 lg:p-8">
              <Navbar />
              <div className="mx-auto max-w-7xl pt-4">
                <MaintenanceDetailsPage />
              </div>
            </div>
          </ProtectedRoute>
      )} />
      <Route path="*" element={<Navigate replace to={home} />} />
    </Routes>
  );
};

const queryClient = new QueryClient();

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

export default App;
