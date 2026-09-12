import type { Metadata } from "next";
import { EB_Garamond, JetBrains_Mono, Lato } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const lato = Lato({
  subsets: ["latin"],
  weight: ["300", "400", "700", "900"],
  variable: "--font-sans",
});
const ebGaramond = EB_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-serif",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "VERITAS",
  description: "Civil Litigation Verification Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn(lato.variable, ebGaramond.variable, jetbrainsMono.variable)}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
