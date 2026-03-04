"""PDF generation for customer engagement intervention reports.

Renders a branded HTML template via Jinja2 and converts to PDF with WeasyPrint.
"""

import os
import tempfile
from datetime import datetime

from jinja2 import Template

try:
    from weasyprint import HTML
except (ImportError, OSError):
    HTML = None


PDF_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 40px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        header {
            border-bottom: 3px solid #4285F4;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #4285F4;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        h2 {
            color: #1f2937;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #4285F4;
            padding-left: 15px;
        }
        .customer-info {
            background: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .metric {
            display: inline-block;
            margin-right: 30px;
            margin-bottom: 10px;
        }
        .metric-label {
            font-weight: 600;
            color: #666;
            font-size: 12px;
        }
        .metric-value {
            font-size: 18px;
            color: #1f2937;
            margin-top: 5px;
        }
        .problem-statement {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .problem-statement strong {
            display: block;
            margin-bottom: 5px;
        }
        .recommendation {
            background: #e8f4f8;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .recommendation strong {
            display: block;
            margin-bottom: 8px;
            color: #004085;
        }
        .content {
            line-height: 1.6;
        }
        .content p {
            margin: 10px 0;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">Cymbal Meet</div>
            <div class="subtitle">Customer Engagement Intervention Report</div>
        </header>

        <div class="customer-info">
            <div class="metric">
                <div class="metric-label">CUSTOMER</div>
                <div class="metric-value">{{ customer_name }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">CUSTOMER ID</div>
                <div class="metric-value">{{ customer_id }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">REPORT DATE</div>
                <div class="metric-value">{{ report_date }}</div>
            </div>
        </div>

        <h2>Engagement Summary</h2>
        <div class="content">
            <p>{{ engagement_summary }}</p>
        </div>

        <h2>Key Metrics</h2>
        <div class="customer-info">
            <div class="metric">
                <div class="metric-label">Login Rate</div>
                <div class="metric-value">{{ login_rate }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Call Duration</div>
                <div class="metric-value">{{ avg_call_duration }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Video Quality</div>
                <div class="metric-value">{{ video_quality }}</div>
            </div>
        </div>

        <h2>Problem Identified</h2>
        <div class="problem-statement">
            <strong>{{ problem_profile }}</strong>
            <p>{{ problem_description }}</p>
        </div>

        <h2>Recommended Actions</h2>
        <div class="content">
            {{ recommendations_html | safe }}
        </div>

        <h2>Relevant Resources</h2>
        <div class="content">
            <p>{{ relevant_resources }}</p>
        </div>

        <footer>
            <p>This report was automatically generated based on engagement data and Vertex AI Search recommendations.</p>
            <p>For more information, contact your Cymbal Meet support team.</p>
        </footer>
    </div>
</body>
</html>
"""


def generate_pdf_from_template(
    customer_id: str,
    customer_name: str,
    problem_profile: str,
    engagement_metrics: dict,
    rag_content: str,
) -> dict:
    """Generate a PDF intervention document and save it to a temp file.

    Returns a file path rather than file content to keep PDF bytes out of
    the LLM context. The caller should pass the file_path to
    upload_to_signed_url after obtaining a signed URL from the GCS MCP server.

    Args:
        customer_id: Customer identifier
        customer_name: Customer display name
        problem_profile: Problem category (e.g., "Declining Usage", "Low Adoption")
        engagement_metrics: Dict with keys like login_rate, avg_call_duration, video_quality
        rag_content: Retrieved content from Vertex AI Search

    Returns:
        dict with file_path (absolute path to the temp PDF) and size_bytes

    Raises:
        ImportError: If WeasyPrint is not installed
    """
    if HTML is None:
        raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")

    metrics_text = "\n".join(f"  {k}: {v}" for k, v in engagement_metrics.items())
    text = (
        f"Intervention Report: {customer_name} ({customer_id})\n\n"
        f"Problem Profile\n{problem_profile}\n\n"
        f"Engagement Metrics\n{metrics_text}\n\n"
        f"Recommendations\n{rag_content}"
    )
    html_content = f"<html><body><pre style='font-family:monospace'>{text}</pre></body></html>"

    pdf_bytes = HTML(string=html_content).write_pdf()

    with tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False, prefix=f"intervention_{customer_id}_"
    ) as f:
        f.write(pdf_bytes)
        file_path = f.name

    return {"file_path": file_path, "size_bytes": len(pdf_bytes)}
    