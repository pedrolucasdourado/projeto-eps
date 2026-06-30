import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AuthProvider } from "@/contexts/auth-context";
import { publicPath } from "@/lib/public-path";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Assistente de Apreensão Inteligente",
  description: "Plataforma de apoio à gestão de apreensões.",
  icons: {
    icon: publicPath("/logo.png"),
  },
};

/** Obrigatório para CSP com nonce por request (Next.js docs). */
export const dynamic = "force-dynamic";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.variable} font-sans`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
