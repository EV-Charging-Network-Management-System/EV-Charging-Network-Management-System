import React from 'react';
import { ConnectorType } from '../types/vehicle';

interface ConnectorSelectorProps {
  connectors: ConnectorType[];
  selectedIds: number[];
  onChange: (selectedIds: number[]) => void;
  disabled?: boolean;
}

export const ConnectorSelector: React.FC<ConnectorSelectorProps> = ({
  connectors,
  selectedIds,
  onChange,
  disabled = false,
}) => {
  const toggleConnector = (id: number) => {
    if (disabled) return;
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((item) => item !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8' }}>
        Supported Connector Standards
      </label>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: '0.75rem',
        }}
      >
        {connectors.map((c) => {
          const isSelected = selectedIds.includes(c.connector_type_id);
          return (
            <div
              key={c.connector_type_id}
              onClick={() => toggleConnector(c.connector_type_id)}
              style={{
                cursor: disabled ? 'not-allowed' : 'pointer',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: isSelected ? '1px solid #79b9ad' : '1px solid #344153',
                backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.1)' : '#19212c',
                transition: 'all 0.15s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600, color: isSelected ? '#79b9ad' : '#f8fafc', fontSize: '0.95rem' }}>
                  {c.type_name}
                </span>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}} // handled by parent div onClick
                  disabled={disabled}
                  style={{ accentColor: '#79b9ad', cursor: disabled ? 'not-allowed' : 'pointer' }}
                />
              </div>
              {c.description && (
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.3 }}>
                  {c.description}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
        Select all ports compatible with your vehicle to ensure accurate charging station matching.
      </p>
    </div>
  );
};

