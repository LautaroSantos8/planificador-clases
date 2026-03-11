import React from 'react';

const NivelBadge = ({ nivel, size = 'md' }) => {
  const config = {
    NEE: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      border: 'border-red-200',
      label: 'NEE',
      description: 'Rezago Significativo',
    },
    LP: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-700',
      border: 'border-yellow-200',
      label: 'LP',
      description: 'Logros en Proceso',
    },
    LE: {
      bg: 'bg-green-100',
      text: 'text-green-700',
      border: 'border-green-200',
      label: 'LE',
      description: 'Logros Esperados',
    },
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const nivelConfig = config[nivel] || config.LE;

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${nivelConfig.bg} ${nivelConfig.text} ${nivelConfig.border} ${sizeClasses[size]}`}
      title={nivelConfig.description}
    >
      {nivelConfig.label}
    </span>
  );
};

export const NivelSelector = ({ value, onChange, disabled = false }) => {
  const niveles = [
    { value: 'NEE', label: 'NEE', description: 'Rezago Significativo', color: 'red' },
    { value: 'LP', label: 'LP', description: 'Logros en Proceso', color: 'yellow' },
    { value: 'LE', label: 'LE', description: 'Logros Esperados', color: 'green' },
  ];

  return (
    <div className="flex gap-2">
      {niveles.map((nivel) => (
        <button
          key={nivel.value}
          type="button"
          onClick={() => onChange(nivel.value)}
          disabled={disabled}
          className={`px-3 py-2 rounded-lg border-2 transition-all ${
            value === nivel.value
              ? nivel.color === 'red'
                ? 'border-red-500 bg-red-50 text-red-700'
                : nivel.color === 'yellow'
                ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                : 'border-green-500 bg-green-50 text-green-700'
              : 'border-gray-200 hover:border-gray-300 text-gray-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          title={nivel.description}
        >
          <span className="font-medium">{nivel.label}</span>
        </button>
      ))}
    </div>
  );
};

export default NivelBadge;
