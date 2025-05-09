'use client';

import ExternalNavbar from './ExternalNavbar';
import InternalNavbar from './InternalNavbar';
import AdminNavbar from './AdminNavbar';
import { usePathname } from 'next/navigation';

export default function NavbarSwitcher() {
  const pathname = usePathname();

  if (!pathname) return null;
  if (pathname.startsWith('/admin-dashboard')) {
    return <AdminNavbar />;
  }
  if (
    pathname.startsWith('/dashboard') ||
    pathname.startsWith('/trades') ||
    pathname.startsWith('/portfolio') ||
    pathname.startsWith('/leaderboard')
  ) {
    return <InternalNavbar />;
  }
  return <ExternalNavbar />;
} 