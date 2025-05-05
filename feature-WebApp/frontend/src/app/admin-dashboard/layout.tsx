import { AdminTabProvider } from '@/components/AdminTabContext';

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  return <AdminTabProvider>{children}</AdminTabProvider>;
} 