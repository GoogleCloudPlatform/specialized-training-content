"""PDF generation for customer engagement intervention reports.

Renders a branded HTML template via Jinja2 and converts to PDF with WeasyPrint.
"""

import os
import re
import tempfile
from datetime import datetime

from jinja2 import Template
from weasyprint import HTML

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
            padding: 48px;
            background: #f8f9fa;
            color: #1a1a2e;
        }
        .container {
            max-width: 780px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        }

        .header-bar {
            height: 6px;
            background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335);
        }
        header {
            padding: 40px 48px 32px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 6px;
        }
        .brand-icon {
            width: 36px;
            height: 36px;
            background: #4285F4;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 18px;
        }
        .brand-name {
            font-size: 22px;
            font-weight: 700;
            color: #1a1a2e;
        }
        .doc-type {
            font-size: 13px;
            font-weight: 500;
            color: #6b7280;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-top: 4px;
            padding-left: 48px;
        }

        .body {
            padding: 0 48px 48px;
        }

        .info-row {
            display: flex;
            gap: 12px;
            margin-bottom: 36px;
        }
        .info-pill {
            background: #f1f5f9;
            border-radius: 10px;
            padding: 14px 20px;
            flex: 1;
        }
        .info-pill .label {
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 4px;
        }
        .info-pill .value {
            font-size: 15px;
            font-weight: 600;
            color: #1e293b;
        }

        h2 {
            font-size: 16px;
            font-weight: 700;
            color: #1a1a2e;
            margin: 32px 0 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }

        .metrics-grid {
            display: flex;
            gap: 16px;
            margin-bottom: 8px;
        }
        .metric-card {
            flex: 1;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .metric-card .num {
            font-size: 28px;
            font-weight: 700;
            color: #4285F4;
        }
        .metric-card .desc {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
            font-weight: 500;
        }

        .focus-callout {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 16px 0;
        }
        .focus-callout .focus-title {
            font-weight: 700;
            color: #1d4ed8;
            margin-bottom: 6px;
            font-size: 15px;
        }
        .focus-callout p {
            margin: 0;
            color: #334155;
            line-height: 1.6;
            font-size: 14px;
        }

        .content {
            font-size: 14px;
            line-height: 1.7;
            color: #374151;
        }
        .content p {
            margin: 10px 0;
        }
        .content ol {
            padding-left: 20px;
            margin: 12px 0;
        }
        .content li {
            margin-bottom: 12px;
            padding-left: 4px;
        }
        .content li strong {
            color: #1e293b;
        }

        .outcomes-box {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 16px 0;
        }
        .outcomes-box p {
            margin: 0;
            color: #166534;
            line-height: 1.6;
            font-size: 14px;
        }

        .content ul {
            padding-left: 20px;
            margin: 12px 0;
        }
        .content ul li {
            margin-bottom: 8px;
            color: #475569;
        }

        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #94a3b8;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar"></div>
        <header>
            <div class="brand">
                <div class="brand-icon">C</div>
                <div class="brand-name">Cymbal Meet</div>
            </div>
            <div class="doc-type">Customer Success Plan</div>
        </header>

        <div class="body">
            <div class="info-row">
                <div class="info-pill">
                    <div class="label">Customer</div>
                    <div class="value">{{ customer_name }}</div>
                </div>
                <div class="info-pill">
                    <div class="label">Customer ID</div>
                    <div class="value">{{ customer_id }}</div>
                </div>
                <div class="info-pill">
                    <div class="label">Report Date</div>
                    <div class="value">{{ report_date }}</div>
                </div>
            </div>

            <h2>Engagement Summary</h2>
            <div class="content">
                <p>{{ engagement_summary }}</p>
            </div>

            <h2>Key Metrics</h2>
            <div class="metrics-grid">
                {% for label, value in metrics %}
                <div class="metric-card">
                    <div class="num">{{ value }}</div>
                    <div class="desc">{{ label }}</div>
                </div>
                {% endfor %}
            </div>

            <h2>Focus Area</h2>
            <div class="focus-callout">
                <div class="focus-title">{{ problem_profile }}</div>
                <p>{{ problem_description }}</p>
            </div>

            <h2>Recommended Actions</h2>
            <div class="content">
                {{ recommendations_html | safe }}
            </div>

            <h2>Expected Outcomes</h2>
            <div class="outcomes-box">
                <p>{{ expected_outcomes }}</p>
            </div>

            <h2>Relevant Resources</h2>
            <div class="content">
                {{ relevant_resources_html | safe }}
            </div>

            <footer>
                <p>This plan was prepared by your Cymbal Meet customer success team using the latest best-practice guidance.</p>
                <p>Questions? Your dedicated account team is here to help — reach out anytime.</p>
            </footer>
        </div>
    </div>
</body>
</html>
"""


def _format_rag_content_as_html(text: str) -> str:
    """Convert plain-text RAG content into structured HTML.

    Handles numbered lists (``1. ...``), bullet lists (``- ...``),
    and section labels ending with a colon (``Key Findings:``).
    Everything else is wrapped in ``<p>`` tags.
    """
    # Normalize: collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text).strip()

    # Detect numbered list items: "1. ...", "2. ..." etc.
    # Split text into: preamble, then numbered items
    numbered_pattern = re.compile(r'(\d+)\.\s+')

    # Find all numbered item positions
    numbered_matches = list(numbered_pattern.finditer(text))

    if not numbered_matches:
        # No numbered list — just handle bullet points and paragraphs
        return _format_bullets_and_paragraphs(text)

    # Everything before the first numbered item is preamble
    preamble = text[:numbered_matches[0].start()].strip()
    html_parts = []

    if preamble:
        html_parts.append(_format_bullets_and_paragraphs(preamble))

    # Extract each numbered item
    html_parts.append('<ol>')
    for i, match in enumerate(numbered_matches):
        start = match.end()
        end = numbered_matches[i + 1].start() if i + 1 < len(numbered_matches) else len(text)
        item_text = text[start:end].strip()
        # Bold the lead-in phrase if it ends with a colon (e.g. "Configure DSCP QoS Markings:")
        item_text = re.sub(
            r'^([^:]{3,60}):\s*',
            r'<strong>\1:</strong> ',
            item_text,
        )
        html_parts.append(f'  <li>{item_text}</li>')
    html_parts.append('</ol>')

    return '\n'.join(html_parts)


def _format_bullets_and_paragraphs(text: str) -> str:
    """Convert ``- item`` bullets into ``<ul>`` and remaining text into ``<p>``."""
    # Split on " - " used as bullet delimiter after sentence-ending punct or colons
    segments = re.split(r'(?<=[.!?:])\s+-\s+|^\s*-\s+', text)

    if len(segments) <= 1:
        # No bullets found — wrap as paragraph
        return f'<p>{text}</p>'

    html_parts = []
    # First segment is preamble before bullets
    preamble = segments[0].strip()
    if preamble:
        html_parts.append(f'<p>{preamble}</p>')

    html_parts.append('<ul>')
    for seg in segments[1:]:
        seg = seg.strip()
        # Strip trailing section labels like "Recommended Remediation Steps:"
        seg = re.sub(r'\s+[A-Z][A-Za-z\s]{3,50}:\s*$', '', seg)
        seg = seg.rstrip('.')
        if seg:
            html_parts.append(f'  <li>{seg}.</li>')
    html_parts.append('</ul>')

    return '\n'.join(html_parts)


def _format_resources_as_html(resources_text: str) -> str:
    """Convert a newline-separated list of resource citations into an HTML list."""
    if not resources_text or not resources_text.strip():
        return "<p>See recommendations above for further details.</p>"
    lines = [line.strip() for line in resources_text.splitlines() if line.strip()]
    if not lines:
        return "<p>See recommendations above for further details.</p>"
    items = "\n".join(f"  <li>{line}</li>" for line in lines)
    return f"<ul>\n{items}\n</ul>"


def generate_pdf_from_template(
    customer_id: str,
    customer_name: str,
    problem_profile: str,
    engagement_metrics: dict,
    rag_content: str,
    expected_outcomes: str = "",
    relevant_resources: str = "",
) -> dict:
    """Generate a PDF customer success plan and save it to a local file.

    Returns a file path rather than file content to keep PDF bytes out of
    the LLM context. The caller should pass the file_path to
    upload_to_signed_url after obtaining a signed URL from the GCS MCP server.

    Args:
        customer_id: Customer identifier
        customer_name: Customer display name
        problem_profile: Focus area (e.g., "Boosting Engagement", "Improving Video Quality")
        engagement_metrics: Dict of metric labels to values (any keys accepted, e.g. login_rate, video_quality_score, network_latency)
        rag_content: Recommended actions text from Vertex AI Search
        expected_outcomes: Paragraph describing positive results the customer can expect
        relevant_resources: Newline-separated list of source documents and sections

    Returns:
        dict with file_path (absolute path to the PDF) and size_bytes

    Raises:
        ImportError: If WeasyPrint is not installed
    """
    if HTML is None:
        raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")

    resources_html = _format_resources_as_html(relevant_resources)

    template = Template(PDF_TEMPLATE)
    html_content = template.render(
        customer_name=customer_name,
        customer_id=customer_id,
        report_date=datetime.now().strftime("%B %d, %Y"),
        engagement_summary=f"This plan outlines tailored recommendations to help {customer_name} get even more value from Cymbal Meet.",
        metrics=[(k.replace("_", " ").title(), v) for k, v in list(engagement_metrics.items())[:3]],
        problem_profile=problem_profile,
        problem_description=f"Based on recent usage patterns, we see a great opportunity to focus on: {problem_profile}.",
        recommendations_html=_format_rag_content_as_html(rag_content),
        expected_outcomes=expected_outcomes or "Follow the recommendations above to improve your team's Cymbal Meet experience.",
        relevant_resources_html=resources_html,
    )

    pdf_bytes = HTML(string=html_content).write_pdf()

    output_dir = os.path.dirname(os.path.abspath(__file__))
    safe_name = customer_name.strip().lower().replace(" ", "-")
    file_path = os.path.join(output_dir, f"{safe_name}_intervention.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    return {"file_path": file_path, "size_bytes": len(pdf_bytes)}
    