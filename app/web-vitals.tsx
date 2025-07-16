"use client"

import { useReportWebVitals } from "next/web-vitals"

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Log to analytics service
    if (typeof window !== "undefined") {
      // Send to your analytics service
      console.log("Web Vital:", metric)

      // Example: Send to Google Analytics
      if (window.gtag) {
        window.gtag("event", metric.name, {
          custom_parameter_1: metric.value,
          custom_parameter_2: metric.id,
          custom_parameter_3: metric.name,
        })
      }

      // Example: Send to custom analytics
      fetch("/api/analytics/web-vitals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(metric),
      }).catch(console.error)
    }
  })

  return null
}
