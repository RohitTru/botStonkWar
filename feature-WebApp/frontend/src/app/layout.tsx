import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ThemeRegistry from '@/theme/ThemeRegistry';
import Navbar from '@/components/Navbar';

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
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <ThemeRegistry>
          <Navbar />
          <main>
            {children}
          </main>
        </ThemeRegistry>
      </body>
    </html>
  );
}
