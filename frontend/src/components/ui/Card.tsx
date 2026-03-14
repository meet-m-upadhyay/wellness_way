import React, { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  padding = 'none',
  shadow = 'md',
  hover = false,
  className = '',
  ...props
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-card dark:shadow-card-dark',
    md: 'shadow-card dark:shadow-card-dark',
    lg: 'shadow-card-hover dark:shadow-card-dark-hover',
  };

  const hoverClass = hover
    ? 'card-hover'
    : '';

  return (
    <div
      className={`
        bg-white dark:bg-wellness-dark-card
        rounded-2xl
        border border-wellness-light-border dark:border-wellness-dark-border
        ${paddingClasses[padding]}
        ${shadowClasses[shadow]}
        ${hoverClass}
        transition-all duration-200
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '' }) => (
  <div className={`border-b border-wellness-light-border dark:border-wellness-dark-border pb-4 mb-4 ${className}`}>
    {children}
  </div>
);

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export const CardTitle: React.FC<CardTitleProps> = ({ children, className = '' }) => (
  <h3 className={`text-lg font-semibold text-wellness-light-text dark:text-wellness-dark-text tracking-tight ${className}`}>
    {children}
  </h3>
);

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({ children, className = '' }) => (
  <div className={className}>
    {children}
  </div>
);

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => (
  <div className={`border-t border-wellness-light-border dark:border-wellness-dark-border pt-4 mt-4 ${className}`}>
    {children}
  </div>
);

export default Card;