"use client"

import type React from "react"

import { useEffect } from "react"

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Skip link functionality
    const skipLink = document.getElementById("skip-to-main")
    const mainContent = document.getElementById("main-content")

    if (skipLink && mainContent) {
      skipLink.addEventListener("click", (e) => {
        e.preventDefault()
        mainContent.focus()
        mainContent.scrollIntoView()
      })
    }

    // Keyboard navigation improvements
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape key to close modals/dropdowns
      if (e.key === "Escape") {
        const activeElement = document.activeElement as HTMLElement
        if (activeElement && activeElement.blur) {
          activeElement.blur()
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <>
      <a
        id="skip-to-main"
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded z-50"
      >
        Skip to main content
      </a>
      <div id="main-content" tabIndex={-1}>
        {children}
      </div>
    </>
  )
}
