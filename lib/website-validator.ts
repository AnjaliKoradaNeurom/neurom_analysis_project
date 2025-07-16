import type { ValidationResult } from "./types"

export class WebsiteValidator {
  async validateWebsite(url: string): Promise<ValidationResult> {
    try {
      console.log(`🔍 Validating website: ${url}`)

      // Step 1: Normalize URL
      const normalizedUrl = this.normalizeUrl(url)
      console.log(`📝 Normalized URL: ${normalizedUrl}`)

      // Step 2: Basic URL validation
      const basicValidation = this.validateUrlFormat(normalizedUrl)
      if (!basicValidation.isValid) {
        return basicValidation
      }

      // Step 3: Check if website is accessible
      const accessibilityCheck = await this.checkWebsiteAccessibility(normalizedUrl)
      if (!accessibilityCheck.isValid) {
        return accessibilityCheck
      }

      // Step 4: Google Search verification (if available)
      const googleVerification = await this.verifyWithGoogleSearch(normalizedUrl)

      // Step 5: Combine results
      const finalResult: ValidationResult = {
        isValid: true,
        normalizedUrl,
        confidence: Math.min(accessibilityCheck.confidence || 0, googleVerification.confidence || 0),
        details: `Website validated successfully. ${googleVerification.details || ""}`,
        statusCode: accessibilityCheck.statusCode,
        googleResults: googleVerification.googleResults,
        dnsResolved: true,
        responseTime: accessibilityCheck.responseTime,
        validationMethod: "comprehensive",
      }

      console.log(`✅ Validation successful for ${url} - Confidence: ${(finalResult.confidence * 100).toFixed(1)}%`)
      return finalResult
    } catch (error) {
      console.error(`❌ Validation failed for ${url}:`, error)
      return {
        isValid: false,
        error: error instanceof Error ? error.message : "Validation failed",
        confidence: 0,
        validationMethod: "error",
      }
    }
  }

  private normalizeUrl(url: string): string {
    try {
      // Remove whitespace
      url = String(url).trim()

      // Add protocol if missing
      if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = `https://${url}`
      }

      // Create URL object to validate and normalize
      const urlObj = new URL(url)

      // Return normalized URL
      return urlObj.toString()
    } catch (error) {
      throw new Error(`Invalid URL format: ${url}`)
    }
  }

  private validateUrlFormat(url: string): ValidationResult {
    try {
      const urlObj = new URL(url)

      // Check for valid protocols
      if (!["http:", "https:"].includes(urlObj.protocol)) {
        return {
          isValid: false,
          error: "Only HTTP and HTTPS protocols are supported",
          confidence: 0,
        }
      }

      // Check for valid hostname
      if (!urlObj.hostname || urlObj.hostname.length === 0) {
        return {
          isValid: false,
          error: "Invalid hostname",
          confidence: 0,
        }
      }

      // Basic hostname validation
      const hostnameRegex =
        /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
      if (!hostnameRegex.test(urlObj.hostname)) {
        return {
          isValid: false,
          error: "Invalid hostname format",
          confidence: 0,
        }
      }

      return {
        isValid: true,
        confidence: 0.8,
        details: "URL format is valid",
      }
    } catch (error) {
      return {
        isValid: false,
        error: "Invalid URL format",
        confidence: 0,
      }
    }
  }

  private async checkWebsiteAccessibility(url: string): Promise<ValidationResult> {
    const startTime = Date.now()

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

      const response = await fetch(url, {
        method: "HEAD", // Use HEAD request for faster validation
        headers: {
          "User-Agent": "Mozilla/5.0 (compatible; WebAuditBot/2.0; +https://webaudit.tool)",
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      const responseTime = Date.now() - startTime

      if (!response.ok) {
        // Try GET request if HEAD fails
        try {
          const getResponse = await fetch(url, {
            headers: {
              "User-Agent": "Mozilla/5.0 (compatible; WebAuditBot/2.0; +https://webaudit.tool)",
            },
            signal: controller.signal,
          })

          if (!getResponse.ok) {
            return {
              isValid: false,
              error: `Website returned ${getResponse.status}: ${getResponse.statusText}`,
              confidence: 0,
              statusCode: getResponse.status,
              responseTime,
            }
          }

          return {
            isValid: true,
            confidence: 0.9,
            details: "Website is accessible",
            statusCode: getResponse.status,
            responseTime,
          }
        } catch (getError) {
          return {
            isValid: false,
            error: `Website is not accessible: ${getError instanceof Error ? getError.message : "Unknown error"}`,
            confidence: 0,
            statusCode: response.status,
            responseTime,
          }
        }
      }

      return {
        isValid: true,
        confidence: 0.9,
        details: "Website is accessible",
        statusCode: response.status,
        responseTime,
      }
    } catch (error) {
      const responseTime = Date.now() - startTime

      if (error instanceof Error && error.name === "AbortError") {
        return {
          isValid: false,
          error: "Website request timeout",
          confidence: 0,
          responseTime,
        }
      }

      return {
        isValid: false,
        error: `Website accessibility check failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        confidence: 0,
        responseTime,
      }
    }
  }

  private async verifyWithGoogleSearch(url: string): Promise<Partial<ValidationResult>> {
    try {
      // Extract domain from URL for search
      const urlObj = new URL(url)
      const domain = urlObj.hostname

      // Mock Google search verification (replace with actual Google Custom Search API)
      // For now, return high confidence for HTTPS sites with valid domains
      const isHttps = url.startsWith("https://")
      const hasValidDomain = domain.includes(".") && !domain.startsWith("localhost")

      if (isHttps && hasValidDomain) {
        return {
          confidence: 0.85,
          details: "Domain appears legitimate based on basic checks",
          googleResults: [], // Would contain actual search results
        }
      }

      return {
        confidence: 0.6,
        details: "Limited verification available",
        googleResults: [],
      }
    } catch (error) {
      console.warn("Google verification failed:", error)
      return {
        confidence: 0.7,
        details: "Google verification unavailable, using basic validation",
        googleResults: [],
      }
    }
  }
}
