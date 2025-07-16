export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics: Map<string, number[]> = new Map()

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  startTimer(label: string): () => number {
    const start = performance.now()
    return () => {
      const duration = performance.now() - start
      this.recordMetric(label, duration)
      return duration
    }
  }

  recordMetric(label: string, value: number): void {
    if (!this.metrics.has(label)) {
      this.metrics.set(label, [])
    }
    this.metrics.get(label)!.push(value)

    // Keep only last 100 measurements
    const values = this.metrics.get(label)!
    if (values.length > 100) {
      values.shift()
    }
  }

  getMetrics(label: string): { avg: number; min: number; max: number; count: number } | null {
    const values = this.metrics.get(label)
    if (!values || values.length === 0) return null

    return {
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      count: values.length,
    }
  }

  getAllMetrics(): Record<string, ReturnType<typeof this.getMetrics>> {
    const result: Record<string, ReturnType<typeof this.getMetrics>> = {}
    for (const [label] of this.metrics) {
      result[label] = this.getMetrics(label)
    }
    return result
  }
}

// Usage example
export function withPerformanceMonitoring<T extends (...args: any[]) => any>(fn: T, label: string): T {
  return ((...args: any[]) => {
    const monitor = PerformanceMonitor.getInstance()
    const endTimer = monitor.startTimer(label)

    try {
      const result = fn(...args)

      if (result instanceof Promise) {
        return result.finally(() => endTimer())
      }

      endTimer()
      return result
    } catch (error) {
      endTimer()
      throw error
    }
  }) as T
}
