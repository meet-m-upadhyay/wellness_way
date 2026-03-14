import React from 'react';
import Navigation from './Navigation';

interface HeaderProps {
  className?: string;
}

const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  return (
    <header className={`sticky top-0 z-50 ${className}`}>
      <div className="glass border-b border-wellness-light-border dark:border-wellness-dark-border shadow-nav">
        <Navigation />
      </div>
    </header>
  );
};

export default Header;