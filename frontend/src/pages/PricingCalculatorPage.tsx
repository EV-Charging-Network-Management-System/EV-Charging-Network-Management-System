import React from 'react';
import { PricingCalculator } from '../components/pricing/PricingCalculator';

export const PricingCalculatorPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">EV Dynamic Pricing & Cost Estimator</h1>
        <p className="text-gray-600 mt-2 text-sm">
          Simulate charging session costs with transparent pricing breakdowns, real-time station demand, and peak-hour rate projections.
        </p>
      </div>

      <PricingCalculator />
    </div>
  );
};

