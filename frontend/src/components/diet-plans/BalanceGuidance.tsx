import React from 'react';
import { BalanceGuidance as BalanceGuidanceType } from '../../services/api';

interface BalanceGuidanceProps {
  guidance: BalanceGuidanceType;
  className?: string;
}

export const BalanceGuidance: React.FC<BalanceGuidanceProps> = ({ guidance, className = '' }) => {
  const getIconColor = () => {
    if (guidance.type === 'warning') return 'text-amber-500';
    return 'text-blue-500';
  };

  const getBgColor = () => {
    if (guidance.type === 'warning') return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';
    return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
  };

  const getTextColor = () => {
    if (guidance.type === 'warning') return 'text-amber-800 dark:text-amber-200';
    return 'text-blue-800 dark:text-blue-200';
  };

  return (
    <div className={`rounded-lg border p-4 ${getBgColor()} ${className}`}>
      <div className="flex items-start space-x-3">
        <div className={`flex-shrink-0 ${getIconColor()}`}>
          {guidance.type === 'warning' ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          <h4 className={`text-sm font-medium ${getTextColor()}`}>
            {guidance.type === 'warning' ? 'Balance Suggestion' : 'Optional Balance Tips'}
          </h4>
          <p className={`mt-1 text-sm ${getTextColor()}`}>
            {guidance.message}
          </p>
          
          {/* Show deltas if significant */}
          {(Math.abs(guidance.calorie_delta) > 50 || Math.abs(guidance.protein_delta) > 3) && (
            <div className={`mt-2 text-xs ${getTextColor()} opacity-75`}>
              <div className="flex space-x-4">
                {Math.abs(guidance.calorie_delta) > 50 && (
                  <span>
                    Calories: {guidance.calorie_delta > 0 ? '+' : ''}{guidance.calorie_delta.toFixed(0)} kcal
                  </span>
                )}
                {Math.abs(guidance.protein_delta) > 3 && (
                  <span>
                    Protein: {guidance.protein_delta > 0 ? '+' : ''}{guidance.protein_delta.toFixed(1)}g
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BalanceGuidance;