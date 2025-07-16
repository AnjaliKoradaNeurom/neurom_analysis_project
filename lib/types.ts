// Updated types to match backend API response
export interface Recommendation {
  priority: string
  title: string
  message: string
  codeSnippet?: string
  docLink?: string
}

export interface ModuleResult {
  name: string
  score: number
  description: string
  explanation: string
  recommendations: Recommendation[]
}

export interface AnalysisResult {
  url: string
  timestamp: string
  overall_score: number
  modules: ModuleResult[]
  analysis_time: number
}

export interface BackendStatus {
  status: string
  backend?: any
  error?: string
}
