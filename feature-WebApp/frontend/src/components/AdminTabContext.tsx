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

export const DASHBOARD_LINKS = [
  { name: 'Web Scraper Engine', url: 'https://feature-webscraperstockselector.emerginary.com/' },
  { name: 'Sentiment Analysis Engine', url: 'https://feature-sentimentanalysisengine.emerginary.com/' },
  { name: 'Trade Recommendation Engine', url: 'https://feature-tradelogistics.emerginary.com/' },
  { name: 'Brokerage Handler Engine', url: 'https://feature-stockbot.emerginary.com/' },
]; 