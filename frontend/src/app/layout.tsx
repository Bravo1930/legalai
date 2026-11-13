import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LegalAI México - Plataforma de Inteligencia Artificial Jurídica",
  description: "Plataforma empresarial para revisión, análisis, extracción y gestión de documentos jurídicos en México.",
};

export default function RootLayout({
  children,
}: ReadexpectChildren<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}

type ReadexpectChildren<T> = T;
