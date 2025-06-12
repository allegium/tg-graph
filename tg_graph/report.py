from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from typing import Dict


def build_pdf(graph_image: str, metrics: Dict[str, float], path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph('Telegram Chat Report', styles['Title']), Spacer(1, 12)]
    story.append(Image(graph_image, width=400, height=300))
    story.append(Spacer(1, 12))
    for key, value in metrics.items():
        story.append(Paragraph(f'{key}: {value}', styles['Normal']))
    doc.build(story)
