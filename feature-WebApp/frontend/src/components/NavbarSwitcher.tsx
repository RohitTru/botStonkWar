'use client';

import ExternalNavbar from './ExternalNavbar';
import InternalNavbar from './InternalNavbar';
import AdminNavbar from './AdminNavbar';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function NavbarSwitcher() {
  const pathname = usePathname();
  const [adminTab, setAdminTab] = useState(0);

  if (!pathname) return null;
  if (pathname.startsWith('/admin-dashboard')) {
    return <AdminNavbar activeIndex={adminTab} setActiveIndex={setAdminTab} />;
  }
  if (pathname.startsWith('/dashboard')) {
    return <InternalNavbar />;
  } else {
    return <ExternalNavbar />;
  }
} 