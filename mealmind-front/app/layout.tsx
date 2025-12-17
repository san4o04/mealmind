import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MealMind",
  description: "MealMind Front",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white">
        {children}
      </body>
    </html>
  );
}
