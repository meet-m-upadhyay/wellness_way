import React from 'react';
import Navigation from './Navigation';

interface HeaderProps {
  className?: string;
}

const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  return (
    <header className={`sticky top-0 z-50 ${className}`}>
      <Navigation />
    </header>
  );
};

export default Header;