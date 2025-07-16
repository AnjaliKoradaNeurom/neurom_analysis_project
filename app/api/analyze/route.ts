import { type NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url } = body

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Forward request to Python backend
    const response = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(30000), // 30 second timeout
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        {
          error: `Backend analysis failed: ${response.status} ${response.statusText}`,
          details: errorData.detail || "Unknown backend error",
        },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("API route error:", error)

    if (error instanceof Error) {
      if (error.name === "TimeoutError") {
        return NextResponse.json({ error: "Backend request timeout. Please try again." }, { status: 504 })
      }

      if (error.message.includes("ECONNREFUSED") || error.message.includes("fetch failed")) {
        return NextResponse.json(
          { error: "Backend service unavailable. Please ensure the Python API is running on port 8000." },
          { status: 503 },
        )
      }
    }

    return NextResponse.json(
      { error: "Internal server error occurred while processing your request." },
      { status: 500 },
    )
  }
}

// Health check endpoint
export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      signal: AbortSignal.timeout(5000),
    })

    if (response.ok) {
      const data = await response.json()
      return NextResponse.json({
        status: "Backend connected",
        backend: data,
      })
    } else {
      return NextResponse.json({ status: "Backend unhealthy", code: response.status }, { status: 503 })
    }
  } catch (error) {
    return NextResponse.json(
      { status: "Backend unavailable", error: error instanceof Error ? error.message : "Unknown error" },
      { status: 503 },
    )
  }
}
