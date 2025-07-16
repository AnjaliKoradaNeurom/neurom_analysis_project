"""
Export manager for generating reports in various formats
"""

import asyncio
import logging
import json
import csv
import io
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class ExportManager:
    """
    Generate reports in PDF, CSV, and JSON formats
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        logger.info("📊 Export manager initialized")
    
    async def generate_pdf_report(self, analysis_data: Dict[str, Any]) -> bytes:
        """
        Generate PDF report from analysis data
        """
        try:
            logger.info("📄 Generating PDF report")
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Title
            title = Paragraph("Website Analysis Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Basic information
            url = analysis_data.get('url', 'Unknown')
            timestamp = analysis_data.get('timestamp', datetime.now().isoformat())
            score = analysis_data.get('crawlability_score', 0)
            
            info_data = [
                ['Website URL:', url],
                ['Analysis Date:', timestamp],
                ['Overall Score:', f"{score:.1f}%"],
                ['Confidence:', f"{analysis_data.get('confidence', 0) * 100:.1f}%"],
                ['Label:', analysis_data.get('label', 'Unknown')]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Recommendations
            recommendations = analysis_data.get('recommendations', [])
            if recommendations:
                rec_title = Paragraph("Recommendations", self.styles['Heading2'])
                story.append(rec_title)
                story.append(Spacer(1, 10))
                
                for i, rec in enumerate(recommendations[:10], 1):
                    rec_text = f"<b>{i}. {rec.get('title', 'Unknown')}</b><br/>"
                    rec_text += f"Priority: {rec.get('priority', 'Medium')}<br/>"
                    rec_text += f"{rec.get('message', 'No description available')}"
                    
                    rec_para = Paragraph(rec_text, self.styles['Normal'])
                    story.append(rec_para)
                    story.append(Spacer(1, 10))
            
            # Technical details
            features = analysis_data.get('features', {})
            if features:
                tech_title = Paragraph("Technical Details", self.styles['Heading2'])
                story.append(tech_title)
                story.append(Spacer(1, 10))
                
                # Create table of key metrics
                tech_data = [['Metric', 'Value']]
                
                key_metrics = [
                    ('Status Code', features.get('status_code', 'Unknown')),
                    ('HTTPS Enabled', 'Yes' if features.get('https_enabled') else 'No'),
                    ('Page Load Time', f"{features.get('page_load_time', 0):.2f}s"),
                    ('HTML Size', f"{features.get('html_size', 0):,} bytes"),
                    ('Word Count', f"{features.get('word_count', 0):,}"),
                    ('Images Count', features.get('images_count', 0)),
                    ('Internal Links', features.get('internal_links_count', 0)),
                    ('External Links', features.get('external_links_count', 0)),
                    ('Mobile Friendly', 'Yes' if features.get('mobile_friendly') else 'No'),
                    ('Robots.txt Exists', 'Yes' if features.get('robots_txt_exists') else 'No')
                ]
                
                for metric, value in key_metrics:
                    tech_data.append([metric, str(value)])
                
                tech_table = Table(tech_data, colWidths=[3*inch, 2*inch])
                tech_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(tech_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info("✅ PDF report generated successfully")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {str(e)}")
            raise
    
    async def generate_csv_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate CSV report from analysis data
        """
        try:
            logger.info("📊 Generating CSV report")
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Website Analysis Report'])
            writer.writerow([])
            
            # Basic info
            writer.writerow(['Basic Information'])
            writer.writerow(['URL', analysis_data.get('url', 'Unknown')])
            writer.writerow(['Analysis Date', analysis_data.get('timestamp', '')])
            writer.writerow(['Overall Score', f"{analysis_data.get('crawlability_score', 0):.1f}%"])
            writer.writerow(['Confidence', f"{analysis_data.get('confidence', 0) * 100:.1f}%"])
            writer.writerow(['Label', analysis_data.get('label', 'Unknown')])
            writer.writerow([])
            
            # Recommendations
            recommendations = analysis_data.get('recommendations', [])
            if recommendations:
                writer.writerow(['Recommendations'])
                writer.writerow(['Priority', 'Title', 'Message'])
                
                for rec in recommendations:
                    writer.writerow([
                        rec.get('priority', 'Medium'),
                        rec.get('title', 'Unknown'),
                        rec.get('message', 'No description')
                    ])
                writer.writerow([])
            
            # Technical features
            features = analysis_data.get('features', {})
            if features:
                writer.writerow(['Technical Details'])
                writer.writerow(['Metric', 'Value'])
                
                for key, value in features.items():
                    if value is not None:
                        writer.writerow([key.replace('_', ' ').title(), str(value)])
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info("✅ CSV report generated successfully")
            return csv_content
            
        except Exception as e:
            logger.error(f"❌ CSV generation failed: {str(e)}")
            raise
    
    async def generate_json_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate JSON report from analysis data
        """
        try:
            logger.info("📋 Generating JSON report")
            
            # Add metadata
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "format_version": "1.0",
                    "generator": "Neurom AI Website Analyzer"
                },
                "analysis_data": analysis_data
            }
            
            json_content = json.dumps(report_data, indent=2, ensure_ascii=False)
            
            logger.info("✅ JSON report generated successfully")
            return json_content
            
        except Exception as e:
            logger.error(f"❌ JSON generation failed: {str(e)}")
            raise
