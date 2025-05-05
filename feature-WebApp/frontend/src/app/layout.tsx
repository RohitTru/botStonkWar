import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ThemeRegistry from '@/theme/ThemeRegistry';
import ExternalNavbar from '@/components/ExternalNavbar';
import InternalNavbar from '@/components/InternalNavbar';
import { usePathname } from 'next/navigation';

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "BotStonkWar",
  description: "A platform for automated trading and community-driven investment strategies",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  let navbar = null;
  if (pathname.startsWith('/dashboard')) {
    navbar = <InternalNavbar />;
  } else if (!pathname.startsWith('/admin-dashboard')) {
    navbar = <ExternalNavbar />;
  }
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <ThemeRegistry>
          {navbar}
          <main>
            {children}
          </main>
        </ThemeRegistry>
      </body>
    </html>
  );
}
