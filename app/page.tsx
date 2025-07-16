import type { Metadata } from "next"
import WebAuditToolClient from "./client_page"

export const metadata: Metadata = {
  title: "Production Website Audit Tool - Real-time SEO & Performance Analysis",
  description:
    "Advanced website analysis with Google verification, real-time crawlability scoring, performance metrics, and actionable SEO recommendations for legitimate websites.",
  keywords: "website audit, SEO analysis, performance testing, crawlability, Google verification",
  authors: [{ name: "Web Audit Tool" }],
  openGraph: {
    title: "Production Website Audit Tool",
    description: "Advanced real-time website analysis with Google verification",
    type: "website",
    url: "https://yoursite.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "Production Website Audit Tool",
    description: "Advanced real-time website analysis with Google verification",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
}

export default function HomePage() {
  return <WebAuditToolClient />
}
