import type { AuditModule, AuditResult, Recommendation } from "./types"
import { WebsiteValidator } from "./website-validator"

export class AuditEngine {
  private validator: WebsiteValidator

  constructor() {
    this.validator = new WebsiteValidator()
  }

  async auditWebsite(url: string): Promise<AuditResult> {
    const startTime = Date.now()

    try {
      console.log(`🔍 Starting audit for: ${url}`)

      // Step 1: Validate the website
      const validationResult = await this.validator.validateWebsite(url)

      if (!validationResult.isValid) {
        console.log(`❌ Validation failed for ${url}: ${validationResult.error}`)
        return {
          url,
          timestamp: new Date().toISOString(),
          overallScore: 0,
          modules: [],
          crawlability_score: 0,
          confidence: 0,
          label: "Invalid Website",
          features: {},
          recommendations: [],
          analysis_time: (Date.now() - startTime) / 1000,
          model_version: "v2.0-production",
          backend: "Next.js",
          error: validationResult.error,
          validationResult,
        }
      }

      console.log(`✅ Validation passed for ${url}, proceeding with analysis`)

      // Step 2: Perform comprehensive analysis on validated website
      const analysisResult = await this.performComprehensiveAnalysis(validationResult.normalizedUrl || url)

      // Step 3: Combine validation and analysis results
      const result: AuditResult = {
        ...analysisResult,
        validationResult,
        confidence: Math.min(validationResult.confidence, analysisResult.confidence),
        analysis_time: (Date.now() - startTime) / 1000,
      }

      console.log(`✅ Complete audit finished for ${url} - Score: ${result.overallScore}%`)
      return result
    } catch (error) {
      console.error(`❌ Audit failed for ${url}:`, error)

      return {
        url,
        timestamp: new Date().toISOString(),
        overallScore: 0,
        modules: [],
        crawlability_score: 0,
        confidence: 0,
        label: "Analysis Failed",
        features: {},
        recommendations: [],
        analysis_time: (Date.now() - startTime) / 1000,
        model_version: "v2.0-production",
        backend: "Next.js",
        error: error instanceof Error ? error.message : "Unknown error occurred",
        validationResult: {
          isValid: false,
          error: "Analysis failed",
          confidence: 0,
        },
      }
    }
  }

  private async performComprehensiveAnalysis(url: string): Promise<Omit<AuditResult, "validationResult">> {
    console.log(`🔬 Performing comprehensive analysis for: ${url}`)

    try {
      // Fetch website content and metadata
      const websiteData = await this.fetchWebsiteData(url)

      // Analyze different aspects
      const seoModule = await this.analyzeSEO(websiteData)
      const performanceModule = await this.analyzePerformance(websiteData)
      const securityModule = await this.analyzeSecurity(websiteData)
      const mobileModule = await this.analyzeMobile(websiteData)
      const crawlabilityModule = await this.analyzeCrawlability(websiteData)

      const modules = [seoModule, performanceModule, securityModule, mobileModule, crawlabilityModule]

      // Calculate overall score
      const overallScore = Math.round(modules.reduce((sum, module) => sum + (module.score || 0), 0) / modules.length)

      // Generate comprehensive recommendations
      const recommendations = this.generateRecommendations(modules, websiteData)

      // Determine label based on score
      const label = this.getScoreLabel(overallScore)

      return {
        url,
        timestamp: new Date().toISOString(),
        overallScore,
        modules,
        crawlability_score: crawlabilityModule.score || 0,
        confidence: 0.85, // High confidence for validated websites
        label,
        features: websiteData.features,
        recommendations,
        analysis_time: 0, // Will be calculated by caller
        model_version: "v2.0-production",
        backend: "Next.js",
      }
    } catch (error) {
      console.error(`❌ Analysis failed:`, error)
      throw error
    }
  }

  private async fetchWebsiteData(url: string) {
    const startTime = Date.now()

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 15000) // 15 second timeout

      const response = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (compatible; WebAuditBot/2.0; +https://webaudit.tool)",
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.5",
          "Accept-Encoding": "gzip, deflate",
          Connection: "keep-alive",
          "Upgrade-Insecure-Requests": "1",
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Check content type
      const contentType = response.headers.get("content-type") || ""
      if (!contentType.includes("text/html")) {
        throw new Error(`Invalid content type: ${contentType}. Expected HTML content.`)
      }

      const content = await response.text()
      const loadTime = (Date.now() - startTime) / 1000

      // Validate that we got HTML content
      const trimmedContent = content.trim().toLowerCase()
      if (!trimmedContent.startsWith("<!doctype") && !trimmedContent.startsWith("<html")) {
        throw new Error("Response does not appear to be valid HTML content")
      }

      // Extract features from content
      const features = this.extractFeatures(content, response, loadTime)

      return {
        url,
        content,
        response,
        features,
        loadTime,
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Request timeout - website took too long to respond")
      }
      throw new Error(`Failed to fetch website data: ${error instanceof Error ? error.message : "Unknown error"}`)
    }
  }

  private extractFeatures(content: string, response: Response, loadTime: number) {
    const features: Record<string, any> = {}

    try {
      // Basic metrics - ensure all are numbers
      features.status_code = Number.parseInt(String(response.status)) || 0
      features.page_load_time = Number.parseFloat(String(loadTime)) || 0
      features.content_length = Number.parseInt(String(content.length)) || 0

      // Clean content for word count (remove HTML tags and extra whitespace)
      const cleanContent = content
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "") // Remove script tags and content
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "") // Remove style tags and content
        .replace(/<[^>]*>/g, " ") // Remove all HTML tags
        .replace(/\s+/g, " ") // Replace multiple whitespace with single space
        .trim()

      const words = cleanContent.split(/\s+/).filter((word) => word.length > 0)
      features.word_count = Number.parseInt(String(words.length)) || 0

      // SSL/HTTPS - ensure boolean
      features.ssl_certificate_valid = Boolean(response.url.startsWith("https://"))

      // HTML structure analysis (case-insensitive) - ensure boolean
      features.has_title = Boolean(/<title[^>]*>.*?<\/title>/i.test(content))
      features.has_meta_description = Boolean(/<meta\s+name=["']description["']/i.test(content))
      features.has_h1 = Boolean(/<h1[^>]*>.*?<\/h1>/i.test(content))
      features.has_viewport = Boolean(/<meta\s+name=["']viewport["']/i.test(content))

      // Count elements - ensure numbers
      const imageMatches = content.match(/<img[^>]*>/gi)
      features.images_count = Number.parseInt(String(imageMatches ? imageMatches.length : 0)) || 0

      const internalLinkMatches = content.match(/<a\s+[^>]*href=["'][^"']*["'][^>]*>/gi)
      features.internal_links_count = Number.parseInt(String(internalLinkMatches ? internalLinkMatches.length : 0)) || 0

      const externalLinkMatches = content.match(/<a\s+[^>]*href=["']https?:\/\/[^"']*["'][^>]*>/gi)
      features.external_links_count = Number.parseInt(String(externalLinkMatches ? externalLinkMatches.length : 0)) || 0

      // SEO elements - ensure boolean
      features.meta_keywords = Boolean(/<meta\s+name=["']keywords["']/i.test(content))
      features.canonical_url = Boolean(/<link\s+rel=["']canonical["']/i.test(content))
      features.robots_meta = Boolean(/<meta\s+name=["']robots["']/i.test(content))

      // Performance indicators - ensure boolean and numbers
      features.has_css = Boolean(/<link[^>]*rel=["']stylesheet["']/i.test(content) || /<style[^>]*>/i.test(content))
      features.has_javascript = Boolean(/<script[^>]*>/i.test(content))

      const inlineCssMatches = content.match(/<style[^>]*>/gi)
      features.inline_css_count = Number.parseInt(String(inlineCssMatches ? inlineCssMatches.length : 0)) || 0

      const inlineJsMatches = content.match(/<script[^>]*>(?!.*src=)/gi)
      features.inline_js_count = Number.parseInt(String(inlineJsMatches ? inlineJsMatches.length : 0)) || 0

      // Mobile indicators - ensure boolean
      features.responsive_design = Boolean(/<meta\s+name=["']viewport["'][^>]*width=device-width/i.test(content))

      // Security headers (from response) - ensure boolean
      features.content_security_policy = Boolean(response.headers.get("content-security-policy"))
      features.x_frame_options = Boolean(response.headers.get("x-frame-options"))
      features.strict_transport_security = Boolean(response.headers.get("strict-transport-security"))

      // Additional content analysis - ensure boolean
      features.has_favicon = Boolean(/<link[^>]*rel=["'][^"']*icon[^"']*["']/i.test(content))
      features.has_open_graph = Boolean(/<meta[^>]*property=["']og:/i.test(content))
      features.has_twitter_card = Boolean(/<meta[^>]*name=["']twitter:/i.test(content))
      features.has_schema_markup = Boolean(/application\/ld\+json/i.test(content) || /schema\.org/i.test(content))

      return features
    } catch (error) {
      console.error("Error extracting features:", error)
      // Return basic features if extraction fails
      return {
        status_code: Number.parseInt(String(response.status)) || 0,
        page_load_time: Number.parseFloat(String(loadTime)) || 0,
        content_length: Number.parseInt(String(content.length)) || 0,
        word_count: 0,
        ssl_certificate_valid: Boolean(response.url.startsWith("https://")),
        has_title: false,
        has_meta_description: false,
        has_h1: false,
        has_viewport: false,
        images_count: 0,
        internal_links_count: 0,
        external_links_count: 0,
        meta_keywords: false,
        canonical_url: false,
        robots_meta: false,
        has_css: false,
        has_javascript: false,
        inline_css_count: 0,
        inline_js_count: 0,
        responsive_design: false,
        content_security_policy: false,
        x_frame_options: false,
        strict_transport_security: false,
        has_favicon: false,
        has_open_graph: false,
        has_twitter_card: false,
        has_schema_markup: false,
      }
    }
  }

  private async analyzeSEO(websiteData: any): Promise<AuditModule> {
    const { features, content } = websiteData
    let score = 0
    const recommendations: Recommendation[] = []

    // Title tag (20 points)
    if (features.has_title) {
      const titleMatch = content.match(/<title[^>]*>(.*?)<\/title>/i)
      const title = titleMatch ? String(titleMatch[1]).trim() : ""
      if (title.length > 0) {
        if (title.length >= 30 && title.length <= 60) {
          score += 20
        } else {
          score += 15
          recommendations.push({
            priority: "Medium",
            title: "Optimize Title Length",
            message: `Title is ${title.length} characters. Aim for 30-60 characters for optimal SEO.`,
            codeSnippet: "<title>Your Optimized Page Title (30-60 chars)</title>",
          })
        }
      } else {
        recommendations.push({
          priority: "High",
          title: "Add Page Title Content",
          message: "Your title tag is empty. Add descriptive content.",
          codeSnippet: "<title>Your Page Title Here</title>",
        })
      }
    } else {
      recommendations.push({
        priority: "High",
        title: "Add Page Title",
        message: "Your page is missing a title tag, which is crucial for SEO.",
        codeSnippet: "<title>Your Page Title Here</title>",
      })
    }

    // Meta description (15 points)
    if (features.has_meta_description) {
      score += 15
    } else {
      recommendations.push({
        priority: "High",
        title: "Add Meta Description",
        message: "Add a meta description to improve search engine visibility.",
        codeSnippet: '<meta name="description" content="Your page description here (150-160 characters)">',
      })
    }

    // H1 tag (15 points)
    if (features.has_h1) {
      score += 15
    } else {
      recommendations.push({
        priority: "Medium",
        title: "Add H1 Heading",
        message: "Add an H1 heading to improve content structure and SEO.",
        codeSnippet: "<h1>Your Main Heading</h1>",
      })
    }

    // SSL/HTTPS (20 points)
    if (features.ssl_certificate_valid) {
      score += 20
    } else {
      recommendations.push({
        priority: "High",
        title: "Enable HTTPS",
        message: "Secure your website with SSL certificate for better SEO and security.",
      })
    }

    // Canonical URL (10 points)
    if (features.canonical_url) {
      score += 10
    } else {
      recommendations.push({
        priority: "Low",
        title: "Add Canonical URL",
        message: "Add canonical URL to prevent duplicate content issues.",
        codeSnippet: '<link rel="canonical" href="https://yoursite.com/page">',
      })
    }

    // Content quality (20 points)
    const wordCount = Number.parseInt(String(features.word_count)) || 0
    if (wordCount >= 300) {
      score += wordCount >= 1000 ? 20 : 15
    } else {
      recommendations.push({
        priority: "Medium",
        title: "Increase Content Length",
        message: `Your page has ${wordCount} words. Add more quality content (aim for 300+ words).`,
      })
    }

    return {
      name: "SEO & Metadata",
      score: Math.min(score, 100),
      description: "Search engine optimization and metadata analysis",
      explanation:
        "This module evaluates your website's SEO fundamentals including title tags, meta descriptions, headings, and content quality.",
      recommendations,
    }
  }

  private async analyzePerformance(websiteData: any): Promise<AuditModule> {
    const { features } = websiteData
    let score = 0
    const recommendations: Recommendation[] = []

    // Page load time (40 points)
    const loadTime = Number.parseFloat(String(features.page_load_time)) || 0
    if (loadTime <= 2) {
      score += 40
    } else if (loadTime <= 4) {
      score += 30
    } else if (loadTime <= 6) {
      score += 20
    } else {
      score += 10
      recommendations.push({
        priority: "High",
        title: "Improve Page Load Speed",
        message: `Your page loads in ${loadTime.toFixed(2)}s. Aim for under 2 seconds.`,
      })
    }

    // Content size (20 points)
    const contentLength = Number.parseInt(String(features.content_length)) || 0
    const contentSizeMB = contentLength / (1024 * 1024)
    if (contentSizeMB <= 1) {
      score += 20
    } else if (contentSizeMB <= 2) {
      score += 15
    } else {
      score += 10
      recommendations.push({
        priority: "Medium",
        title: "Optimize Content Size",
        message: `Your page is ${contentSizeMB.toFixed(2)}MB. Consider optimizing images and content.`,
      })
    }

    // CSS optimization (20 points)
    const inlineCssCount = Number.parseInt(String(features.inline_css_count)) || 0
    if (inlineCssCount <= 2) {
      score += 20
    } else {
      score += 10
      recommendations.push({
        priority: "Medium",
        title: "Reduce Inline CSS",
        message: `Found ${inlineCssCount} inline CSS blocks. Move to external stylesheets.`,
      })
    }

    // JavaScript optimization (20 points)
    const inlineJsCount = Number.parseInt(String(features.inline_js_count)) || 0
    if (inlineJsCount <= 2) {
      score += 20
    } else {
      score += 10
      recommendations.push({
        priority: "Medium",
        title: "Optimize JavaScript",
        message: `Found ${inlineJsCount} inline JavaScript blocks. Consider optimization.`,
      })
    }

    return {
      name: "Performance",
      score: Math.min(score, 100),
      description: "Website speed and performance optimization",
      explanation: "This module analyzes your website's loading speed, content size, and resource optimization.",
      recommendations,
    }
  }

  private async analyzeSecurity(websiteData: any): Promise<AuditModule> {
    const { features } = websiteData
    let score = 0
    const recommendations: Recommendation[] = []

    // HTTPS (30 points)
    if (features.ssl_certificate_valid) {
      score += 30
    } else {
      recommendations.push({
        priority: "High",
        title: "Enable HTTPS",
        message: "Secure your website with SSL certificate.",
      })
    }

    // Security headers (70 points total)
    if (features.content_security_policy) {
      score += 25
    } else {
      recommendations.push({
        priority: "Medium",
        title: "Add Content Security Policy",
        message: "Implement CSP header to prevent XSS attacks.",
      })
    }

    if (features.x_frame_options) {
      score += 20
    } else {
      recommendations.push({
        priority: "Medium",
        title: "Add X-Frame-Options Header",
        message: "Prevent clickjacking attacks with X-Frame-Options header.",
      })
    }

    if (features.strict_transport_security) {
      score += 25
    } else {
      recommendations.push({
        priority: "Low",
        title: "Add HSTS Header",
        message: "Implement HTTP Strict Transport Security for enhanced security.",
      })
    }

    return {
      name: "Security",
      score: Math.min(score, 100),
      description: "Website security and protection measures",
      explanation:
        "This module evaluates your website's security headers, SSL implementation, and protection against common vulnerabilities.",
      recommendations,
    }
  }

  private async analyzeMobile(websiteData: any): Promise<AuditModule> {
    const { features } = websiteData
    let score = 0
    const recommendations: Recommendation[] = []

    // Viewport meta tag (40 points)
    if (features.has_viewport) {
      score += 40
    } else {
      recommendations.push({
        priority: "High",
        title: "Add Viewport Meta Tag",
        message: "Add viewport meta tag for mobile responsiveness.",
        codeSnippet: '<meta name="viewport" content="width=device-width, initial-scale=1">',
      })
    }

    // Responsive design (40 points)
    if (features.responsive_design) {
      score += 40
    } else {
      recommendations.push({
        priority: "High",
        title: "Implement Responsive Design",
        message: "Make your website responsive for mobile devices.",
      })
    }

    // Touch-friendly elements (20 points)
    // This is a simplified check - in a real implementation, you'd analyze button sizes, etc.
    score += 20 // Assume touch-friendly for now

    return {
      name: "Mobile Friendliness",
      score: Math.min(score, 100),
      description: "Mobile device compatibility and responsiveness",
      explanation:
        "This module checks if your website is optimized for mobile devices and provides a good user experience on smartphones and tablets.",
      recommendations,
    }
  }

  private async analyzeCrawlability(websiteData: any): Promise<AuditModule> {
    const { features } = websiteData
    let score = 0
    const recommendations: Recommendation[] = []

    // Robots meta (20 points)
    if (features.robots_meta) {
      score += 20
    } else {
      recommendations.push({
        priority: "Low",
        title: "Add Robots Meta Tag",
        message: "Add robots meta tag to control search engine crawling.",
        codeSnippet: '<meta name="robots" content="index, follow">',
      })
    }

    // Internal linking (30 points)
    const internalLinksCount = Number.parseInt(String(features.internal_links_count)) || 0
    if (internalLinksCount >= 5) {
      score += 30
    } else if (internalLinksCount >= 2) {
      score += 20
    } else {
      recommendations.push({
        priority: "Medium",
        title: "Improve Internal Linking",
        message: `Found ${internalLinksCount} internal links. Add more to help search engines discover content.`,
      })
    }

    // Content structure (30 points)
    if (features.has_h1 && features.has_title) {
      score += 30
    } else {
      score += 15
      recommendations.push({
        priority: "Medium",
        title: "Improve Content Structure",
        message: "Use proper heading hierarchy (H1, H2, H3) to structure your content.",
      })
    }

    // Schema markup (20 points)
    if (features.has_schema_markup) {
      score += 20
    } else {
      recommendations.push({
        priority: "Low",
        title: "Add Structured Data",
        message: "Implement schema markup to help search engines understand your content.",
      })
    }

    return {
      name: "Crawlability",
      score: Math.min(score, 100),
      description: "Search engine crawling and indexing optimization",
      explanation: "This module evaluates how easily search engines can crawl and index your website content.",
      recommendations,
    }
  }

  private generateRecommendations(modules: AuditModule[], websiteData: any): Recommendation[] {
    const allRecommendations: Recommendation[] = []

    // Collect all recommendations from modules
    modules.forEach((module) => {
      allRecommendations.push(...module.recommendations)
    })

    // Sort by priority (High -> Medium -> Low)
    const priorityOrder: Record<string, number> = { High: 0, Medium: 1, Low: 2 }
    allRecommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])

    // Return top 10 recommendations
    return allRecommendations.slice(0, 10)
  }

  private getScoreLabel(score: number): string {
    if (score >= 90) return "Excellent"
    if (score >= 80) return "Good"
    if (score >= 60) return "Fair"
    if (score >= 40) return "Poor"
    return "Critical"
  }
}

// Export the audit function for backward compatibility
export async function auditWebsite(url: string): Promise<AuditResult> {
  const engine = new AuditEngine()
  return engine.auditWebsite(url)
}
