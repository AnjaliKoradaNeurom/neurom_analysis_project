"""
Export Manager for generating PDF and CSV reports.
Handles the creation and formatting of analysis reports in various formats.
"""

import os
import csv
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO, StringIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white, red, green, orange
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.schemas import AnalysisResult, Recommendation, ExportFormat


class ExportManager:
    """Manages the export of analysis results to various formats"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.styles = self._setup_styles() if REPORTLAB_AVAILABLE else None
    
    def _setup_styles(self):
        """Setup custom styles for PDF generation"""
        if not REPORTLAB_AVAILABLE:
            return None
            
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#2563eb'),
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=HexColor('#1f2937'),
            borderWidth=1,
            borderColor=HexColor('#e5e7eb'),
            borderPadding=5
        ))
        
        styles.add(ParagraphStyle(
            name='ScoreText',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor('#374151'),
            alignment=TA_CENTER
        ))
        
        return styles
    
    def export_to_pdf(self, analysis_result: AnalysisResult, filename: Optional[str] = None) -> str:
        """
        Export analysis result to PDF format
        
        Args:
            analysis_result: The analysis result to export
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            ImportError: If reportlab is not available
            Exception: If PDF generation fails
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_audit_report_{timestamp}.pdf"
        
        filepath = os.path.join(self.temp_dir, filename)
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            story.append(Paragraph("Web Audit Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            
            # URL and basic info
            story.append(Paragraph(f"<b>Website:</b> {analysis_result.url}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Analysis Date:</b> {analysis_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Analysis ID:</b> {analysis_result.analysis_id}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Overall Score Section
            story.append(Paragraph("Overall Score", self.styles['SectionHeader']))
            
            score_color = self._get_score_color(analysis_result.overall_score)
            story.append(Paragraph(
                f"<font color='{score_color}'><b>{analysis_result.overall_score:.1f}/100 (Grade: {analysis_result.grade})</b></font>",
                self.styles['ScoreText']
            ))
            story.append(Spacer(1, 20))
            
            # Detailed Scores
            if analysis_result.ai_analysis:
                story.append(Paragraph("Detailed Scores", self.styles['SectionHeader']))
                
                scores_data = [
                    ['Category', 'Score', 'Status'],
                    ['SEO', f"{analysis_result.ai_analysis.seo_score:.1f}/100", self._get_status_text(analysis_result.ai_analysis.seo_score)],
                    ['Performance', f"{analysis_result.ai_analysis.performance_score:.1f}/100", self._get_status_text(analysis_result.ai_analysis.performance_score)],
                    ['Security', f"{analysis_result.ai_analysis.security_score:.1f}/100", self._get_status_text(analysis_result.ai_analysis.security_score)],
                    ['Mobile', f"{analysis_result.ai_analysis.mobile_score:.1f}/100", self._get_status_text(analysis_result.ai_analysis.mobile_score)],
                ]
                
                scores_table = Table(scores_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                scores_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), white),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                
                story.append(scores_table)
                story.append(Spacer(1, 20))
            
            # Strengths and Weaknesses
            if analysis_result.ai_analysis:
                if analysis_result.ai_analysis.strengths:
                    story.append(Paragraph("Strengths", self.styles['SectionHeader']))
                    for strength in analysis_result.ai_analysis.strengths:
                        story.append(Paragraph(f"• {strength}", self.styles['Normal']))
                    story.append(Spacer(1, 15))
                
                if analysis_result.ai_analysis.weaknesses:
                    story.append(Paragraph("Areas for Improvement", self.styles['SectionHeader']))
                    for weakness in analysis_result.ai_analysis.weaknesses:
                        story.append(Paragraph(f"• {weakness}", self.styles['Normal']))
                    story.append(Spacer(1, 15))
            
            # Recommendations
            if analysis_result.ai_analysis and analysis_result.ai_analysis.recommendations:
                story.append(PageBreak())
                story.append(Paragraph("Recommendations", self.styles['CustomTitle']))
                story.append(Spacer(1, 20))
                
                # Group recommendations by priority
                recommendations_by_priority = self._group_recommendations_by_priority(
                    analysis_result.ai_analysis.recommendations
                )
                
                for priority in ['critical', 'high', 'medium', 'low']:
                    if priority in recommendations_by_priority:
                        story.append(Paragraph(f"{priority.title()} Priority", self.styles['SectionHeader']))
                        
                        for i, rec in enumerate(recommendations_by_priority[priority], 1):
                            story.append(Paragraph(f"<b>{i}. {rec.title}</b>", self.styles['Normal']))
                            story.append(Paragraph(f"<b>Category:</b> {rec.category}", self.styles['Normal']))
                            story.append(Paragraph(f"<b>Description:</b> {rec.description}", self.styles['Normal']))
                            story.append(Paragraph(f"<b>Impact:</b> {rec.impact}", self.styles['Normal']))
                            story.append(Paragraph(f"<b>Effort:</b> {rec.effort}", self.styles['Normal']))
                            
                            if rec.resources:
                                story.append(Paragraph("<b>Resources:</b>", self.styles['Normal']))
                                for resource in rec.resources:
                                    story.append(Paragraph(f"• {resource}", self.styles['Normal']))
                            
                            story.append(Spacer(1, 15))
                        
                        story.append(Spacer(1, 10))
            
            # Technical Details
            if analysis_result.features:
                story.append(PageBreak())
                story.append(Paragraph("Technical Details", self.styles['CustomTitle']))
                story.append(Spacer(1, 20))
                
                tech_data = [
                    ['Metric', 'Value'],
                    ['Page Size', f"{analysis_result.features.page_size:,} bytes"],
                    ['Load Time', f"{analysis_result.features.load_time:.2f} seconds"],
                    ['Word Count', f"{analysis_result.features.word_count:,}"],
                    ['Image Count', str(analysis_result.features.image_count)],
                    ['Link Count', str(analysis_result.features.link_count)],
                    ['Has SSL', 'Yes' if analysis_result.features.has_ssl else 'No'],
                    ['Mobile Friendly', 'Yes' if analysis_result.features.is_mobile_friendly else 'No'],
                    ['Has Robots.txt', 'Yes' if analysis_result.features.has_robots_txt else 'No'],
                    ['Has Sitemap', 'Yes' if analysis_result.features.has_sitemap else 'No'],
                ]
                
                tech_table = Table(tech_data, colWidths=[3*inch, 2*inch])
                tech_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), white),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                
                story.append(tech_table)
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(HRFlowable(width="100%"))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Web Audit Tool v2.0",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")
    
    def export_to_csv(self, analysis_result: AnalysisResult, filename: Optional[str] = None) -> str:
        """
        Export analysis result to CSV format
        
        Args:
            analysis_result: The analysis result to export
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_audit_data_{timestamp}.csv"
        
        filepath = os.path.join(self.temp_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow(['Metric', 'Value'])
                
                # Basic information
                writer.writerow(['URL', str(analysis_result.url)])
                writer.writerow(['Analysis Date', analysis_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Analysis ID', analysis_result.analysis_id])
                writer.writerow(['Overall Score', f"{analysis_result.overall_score:.1f}"])
                writer.writerow(['Grade', analysis_result.grade])
                writer.writerow(['Processing Time', f"{analysis_result.processing_time:.2f} seconds"])
                
                # AI Analysis scores
                if analysis_result.ai_analysis:
                    writer.writerow(['SEO Score', f"{analysis_result.ai_analysis.seo_score:.1f}"])
                    writer.writerow(['Performance Score', f"{analysis_result.ai_analysis.performance_score:.1f}"])
                    writer.writerow(['Security Score', f"{analysis_result.ai_analysis.security_score:.1f}"])
                    writer.writerow(['Mobile Score', f"{analysis_result.ai_analysis.mobile_score:.1f}"])
                    writer.writerow(['Confidence', f"{analysis_result.ai_analysis.confidence:.3f}"])
                
                # Technical features
                if analysis_result.features:
                    writer.writerow(['Page Size (bytes)', analysis_result.features.page_size])
                    writer.writerow(['Load Time (seconds)', f"{analysis_result.features.load_time:.2f}"])
                    writer.writerow(['Word Count', analysis_result.features.word_count])
                    writer.writerow(['Image Count', analysis_result.features.image_count])
                    writer.writerow(['Link Count', analysis_result.features.link_count])
                    writer.writerow(['Has SSL', 'Yes' if analysis_result.features.has_ssl else 'No'])
                    writer.writerow(['Mobile Friendly', 'Yes' if analysis_result.features.is_mobile_friendly else 'No'])
                    writer.writerow(['Has Robots.txt', 'Yes' if analysis_result.features.has_robots_txt else 'No'])
                    writer.writerow(['Has Sitemap', 'Yes' if analysis_result.features.has_sitemap else 'No'])
                
                # Empty row
                writer.writerow([])
                
                # Recommendations
                if analysis_result.ai_analysis and analysis_result.ai_analysis.recommendations:
                    writer.writerow(['Recommendations'])
                    writer.writerow(['Priority', 'Category', 'Title', 'Description', 'Impact', 'Effort'])
                    
                    for rec in analysis_result.ai_analysis.recommendations:
                        writer.writerow([
                            rec.priority,
                            rec.category,
                            rec.title,
                            rec.description,
                            rec.impact,
                            rec.effort
                        ])
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate CSV: {str(e)}")
    
    def export_to_json(self, analysis_result: AnalysisResult, filename: Optional[str] = None) -> str:
        """
        Export analysis result to JSON format
        
        Args:
            analysis_result: The analysis result to export
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the generated JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_audit_data_{timestamp}.json"
        
        filepath = os.path.join(self.temp_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(
                    analysis_result.dict(),
                    jsonfile,
                    indent=2,
                    default=str,
                    ensure_ascii=False
                )
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate JSON: {str(e)}")
    
    def export(self, analysis_result: AnalysisResult, format: ExportFormat, filename: Optional[str] = None) -> str:
        """
        Export analysis result in the specified format
        
        Args:
            analysis_result: The analysis result to export
            format: Export format (PDF, CSV, or JSON)
            filename: Optional filename
            
        Returns:
            Path to the generated file
        """
        if format == ExportFormat.PDF:
            return self.export_to_pdf(analysis_result, filename)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(analysis_result, filename)
        elif format == ExportFormat.JSON:
            return self.export_to_json(analysis_result, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score"""
        if score >= 80:
            return '#10b981'  # Green
        elif score >= 60:
            return '#f59e0b'  # Yellow
        else:
            return '#ef4444'  # Red
    
    def _get_status_text(self, score: float) -> str:
        """Get status text based on score"""
        if score >= 80:
            return 'Good'
        elif score >= 60:
            return 'Needs Improvement'
        else:
            return 'Poor'
    
    def _group_recommendations_by_priority(self, recommendations: List[Recommendation]) -> Dict[str, List[Recommendation]]:
        """Group recommendations by priority"""
        grouped = {}
        for rec in recommendations:
            priority = rec.priority.lower()
            if priority not in grouped:
                grouped[priority] = []
            grouped[priority].append(rec)
        return grouped
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Clean up temporary export files older than specified hours
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                if filename.startswith(('web_audit_report_', 'web_audit_data_')):
                    filepath = os.path.join(self.temp_dir, filename)
                    file_age = current_time - os.path.getctime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        
        except Exception as e:
            # Log error but don't raise - cleanup is not critical
            print(f"Warning: Failed to cleanup temp files: {e}")
