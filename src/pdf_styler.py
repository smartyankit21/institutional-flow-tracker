import markdown
from weasyprint import HTML, CSS

REPORT_CSS = """
@page {
    size: A4;
    margin: 1.5cm;
    @bottom-right {
        content: counter(page);
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 8pt;
        color: #888;
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    color: #1a1a1a;
    line-height: 1.5;
    font-size: 9.5pt;
}
h1 {
    font-size: 18pt;
    color: #0f172a;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 4px;
    margin-bottom: 8px;
}
h2, h3 {
    font-size: 12pt;
    color: #1e293b;
    margin-top: 14pt;
    margin-bottom: 6pt;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 3px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    font-size: 8.5pt;
}
th, td {
    border: 1px solid #e2e8f0;
    padding: 5pt 7pt;
    text-align: left;
}
th {
    background-color: #f1f5f9;
    font-weight: bold;
    color: #334155;
}
tr:nth-child(even) td {
    background-color: #f8fafc;
}
strong {
    color: #0f172a;
}
hr {
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 14pt 0;
}
"""

def export_to_pdf(markdown_text: str, output_filepath: str):
    html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
    html = HTML(string=html_content)
    css = CSS(string=REPORT_CSS)
    html.write_pdf(output_filepath, stylesheets=[css])
    print(f"[PDF Generated] {output_filepath}")
