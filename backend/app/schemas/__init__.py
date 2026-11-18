"""
Pydantic Schemas Registry.
"""

from backend.app.schemas.common import HealthResponse, DatabaseHealthResponse, APIResponse
from backend.app.schemas.auth import UserRegister, UserLogin, TokenResponse, LogoutResponse
from backend.app.schemas.user import UserBase, UserCreate, UserUpdateProfile, UserStatusUpdate, UserResponse
from backend.app.schemas.vehicle import (
    ConnectorTypeResponse,
    VehicleBase,
    VehicleCreate,
    VehicleUpdate,
    VehicleConnectorUpdate,
    VehicleResponse
)
from backend.app.schemas.station import (
    ChargerBase,
    ChargerCreate,
    ChargerUpdate,
    ChargerResponse,
    StationBase,
    StationCreate,
    StationUpdate,
    StationResponse,
    StationNearbyResponse
)
from backend.app.schemas.tariff import (
    PricingRuleBase,
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRuleResponse,
    TariffBase,
    TariffCreate,
    TariffUpdate,
    TariffResponse,
    AppliedRuleInfo,
    PricingQuoteRequest,
    PricingQuoteResponse,
    StationDemandResponse,
    TariffEstimateRequest,
    TariffEstimateResponse
)
from backend.app.schemas.reservation import (
    ReservationBase,
    ReservationCreate,
    ReservationStatusUpdate,
    ReservationResponse,
    ReservationCancelResponse,
    AvailableChargerResponse,
    ChargerAvailabilityResponse,
    ReservationCustomerInfo,
    ReservationVehicleInfo,
    ReservationStationInfo,
    ReservationChargerInfo
)
from backend.app.schemas.session import (
    SessionStartRequest,
    SessionCompleteRequest,
    SessionInterruptRequest,
    SessionStopRequest,
    SessionResponse,
    SessionCustomerInfo,
    SessionVehicleInfo,
    SessionStationInfo,
    SessionChargerInfo,
    SessionTariffInfo
)
from backend.app.schemas.billing import (
    PaymentCreate,
    PaymentResponse,
    PaymentRefundRequest,
    InvoiceResponse,
    InvoiceCustomerInfo,
    InvoiceStationInfo,
    DailyRevenue,
    MonthlyRevenue,
    StationRevenue,
    PaymentMethodBreakdown,
    RevenueReportResponse
)
from backend.app.schemas.maintenance import MaintenanceCreate, MaintenanceResponse, ChargerStatusHistoryResponse

__all__ = [
    "HealthResponse",
    "DatabaseHealthResponse",
    "APIResponse",
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "LogoutResponse",
    "UserBase",
    "UserCreate",
    "UserUpdateProfile",
    "UserStatusUpdate",
    "UserResponse",
    "ConnectorTypeResponse",
    "VehicleBase",
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleConnectorUpdate",
    "VehicleResponse",
    "ChargerBase",
    "ChargerCreate",
    "ChargerUpdate",
    "ChargerResponse",
    "StationBase",
    "StationCreate",
    "StationUpdate",
    "StationResponse",
    "StationNearbyResponse",
    "PricingRuleResponse",
    "TariffResponse",
    "TariffEstimateRequest",
    "TariffEstimateResponse",
    "ReservationBase",
    "ReservationCreate",
    "ReservationStatusUpdate",
    "ReservationResponse",
    "SessionStartRequest",
    "SessionStopRequest",
    "SessionResponse",
    "PaymentCreate",
    "PaymentResponse",
    "InvoiceResponse",
    "MaintenanceCreate",
    "MaintenanceResponse",
    "ChargerStatusHistoryResponse",
]
