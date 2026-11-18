import React from 'react';
import { PricingCalculator } from '../components/pricing/PricingCalculator';

export const PricingCalculatorPage: React.FC = () => {
  return (
    <div className="pricing-page">
      <div className="pricing-heading">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Charging cost estimator</h1>
        <p className="text-gray-600 mt-2 text-sm">
          Estimate your charging cost using the station tariff and planned start time.
        </p>
      </div>

      <PricingCalculator />
    </div>
  );
};

