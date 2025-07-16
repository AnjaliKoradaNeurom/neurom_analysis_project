"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { FileText, Download } from "lucide-react"

// Updated interface to match backend response
interface AnalysisResult {
  url: string
  timestamp: string
  overall_score: number
  modules: Array<{
    name: string
    score: number
    description: string
    explanation: string
    recommendations: Array<{
      priority: string
      title: string
      message: string
      codeSnippet?: string
      docLink?: string
    }>
  }>
  analysis_time: number
}

interface ExportManagerProps {
  result: AnalysisResult
}

export default function ExportManager({ result }: ExportManagerProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [fileName, setFileName] = useState("")
  const [exportType, setExportType] = useState<"pdf" | "csv" | "json" | null>(null)

  // Only allow export if we have valid backend data
  if (!result || !result.url) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No analysis data available for export</p>
        <p className="text-sm text-gray-400 mt-2">Complete an analysis first to enable export functionality</p>
      </div>
    )
  }

  // Generate default filename based on URL and timestamp
  const generateDefaultFileName = (type: string) => {
    const domain = new URL(result.url).hostname.replace(/[^a-zA-Z0-9]/g, "_")
    const timestamp = new Date().toISOString().split("T")[0]
    return `backend_analysis_${domain}_${timestamp}.${type}`
  }

  // Export to JSON (native JavaScript) - only backend data
  const exportToJSON = (customFileName?: string) => {
    setIsExporting(true)
    try {
      // Create export object with only backend data
      const exportData = {
        metadata: {
          exportedAt: new Date().toISOString(),
          exportVersion: "2.0",
          tool: "Website Audit Tool - Backend API",
          dataSource: "Python FastAPI Backend",
        },
        analysis: {
          url: result.url,
          timestamp: result.timestamp,
          overall_score: result.overall_score,
          analysis_time: result.analysis_time,
        },
        modules: result.modules.map((module) => ({
          name: module.name,
          score: module.score,
          description: module.description,
          explanation: module.explanation,
          recommendations: module.recommendations,
        })),
        summary: {
          total_modules: result.modules.length,
          average_score: result.overall_score,
          total_recommendations: result.modules.reduce((sum, m) => sum + m.recommendations.length, 0),
        },
      }

      // Convert to JSON string with pretty formatting
      const jsonString = JSON.stringify(exportData, null, 2)

      // Create and download the file
      const blob = new Blob([jsonString], { type: "application/json;charset=utf-8;" })
      const link = document.createElement("a")
      const url = URL.createObjectURL(blob)

      link.setAttribute("href", url)
      link.setAttribute("download", customFileName || generateDefaultFileName("json"))
      link.style.visibility = "hidden"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error("JSON export failed:", error)
      alert("Failed to export JSON. Please try again.")
    } finally {
      setIsExporting(false)
    }
  }

  // Handle export with optional filename dialog
  const handleExport = (type: "json") => {
    setExportType(type)
    setFileName(generateDefaultFileName(type))
  }

  // Execute the export
  const executeExport = () => {
    if (!exportType) return

    const customFileName = fileName.trim() || generateDefaultFileName(exportType)

    switch (exportType) {
      case "json":
        exportToJSON(customFileName)
        break
    }

    setExportType(null)
    setFileName("")
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4">
        {/* JSON Export Button - Only option since we only have backend data */}
        <Dialog>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              className="h-20 flex-col bg-transparent hover:bg-gray-50"
              onClick={() => handleExport("json")}
              disabled={isExporting}
            >
              <FileText className="h-6 w-6 mb-2 text-blue-600" />
              <span className="font-medium">JSON Export</span>
              <span className="text-xs text-gray-500">Backend analysis data</span>
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Export Backend Analysis Data</DialogTitle>
              <DialogDescription>
                Export the complete backend analysis data in JSON format for developers and API integrations.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="json-filename">File Name</Label>
                <Input
                  id="json-filename"
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  placeholder={generateDefaultFileName("json")}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={executeExport} disabled={isExporting}>
                {isExporting ? (
                  <>
                    <Download className="h-4 w-4 mr-2 animate-spin" />
                    Generating JSON...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Export Status */}
      {isExporting && (
        <div className="text-center text-sm text-gray-600 flex items-center justify-center">
          <Download className="h-4 w-4 mr-2 animate-spin" />
          Preparing your backend data export...
        </div>
      )}

      {/* Export Information */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>
          <strong>JSON Export:</strong> Raw backend analysis data in JSON format
        </p>
        <p>
          <strong>Data Source:</strong> Python FastAPI backend - no client-side processing
        </p>
        <p>
          <strong>Note:</strong> PDF and CSV exports disabled - only backend data available
        </p>
      </div>
    </div>
  )
}
