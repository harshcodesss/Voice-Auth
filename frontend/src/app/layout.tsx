import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "VoiceAuth — Hindi Speaker Recognition",
  description:
    "AI-powered speaker identification for Hindi audio using SpeechBrain ECAPA embeddings. Register speakers, analyze conversations, and detect unknown voices.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main style={{ paddingTop: 64 }}>{children}</main>
      </body>
    </html>
  );
}
