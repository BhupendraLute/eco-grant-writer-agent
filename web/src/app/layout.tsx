import type { Metadata } from "next";
import { Inter, Fira_Code } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Eco Grant Writer — AI Grant Proposal Assistant",
  description:
    "AI-powered grant proposal assistant for environmental nonprofits. Built with Google ADK 2.0, Gemini LLM, and FastMCP tools.",
  keywords: [
    "grant writer",
    "AI agent",
    "environmental",
    "nonprofit",
    "grant proposal",
    "ADK",
    "Gemini",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${firaCode.variable} h-full antialiased dark`}
    >
      <body suppressHydrationWarning className="h-full">{children}</body>
    </html>
  );
}
