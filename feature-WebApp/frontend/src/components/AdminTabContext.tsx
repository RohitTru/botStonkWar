'use client';
import { createContext, useContext, useState, ReactNode } from 'react';

const AdminTabContext = createContext<{
  activeIndex: number;
  setActiveIndex: (i: number) => void;
}>({
  activeIndex: 0,
  setActiveIndex: () => {},
});

export function AdminTabProvider({ children }: { children: ReactNode }) {
  const [activeIndex, setActiveIndex] = useState(0);
  return (
    <AdminTabContext.Provider value={{ activeIndex, setActiveIndex }}>
      {children}
    </AdminTabContext.Provider>
  );
}

export function useAdminTab() {
  return useContext(AdminTabContext);
} 