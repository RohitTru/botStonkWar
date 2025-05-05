'use client';

import ExternalNavbar from './ExternalNavbar';
import InternalNavbar from './InternalNavbar';
import { usePathname } from 'next/navigation';

export default function NavbarSwitcher() {
  const pathname = usePathname();

  if (!pathname) return null;
  if (pathname.startsWith('/dashboard')) {
    return <InternalNavbar />;
  } else if (!pathname.startsWith('/admin-dashboard')) {
    return <ExternalNavbar />;
  }
  return null;
} 