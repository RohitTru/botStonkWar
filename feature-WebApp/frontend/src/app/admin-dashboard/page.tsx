import { AdminTabProvider } from '@/components/AdminTabContext';
import AdminDashboard from '@/components/dashboard/AdminDashboard';

export default function AdminDashboardPage() {
  return (
    <AdminTabProvider>
      <AdminDashboard />
    </AdminTabProvider>
  );
} 