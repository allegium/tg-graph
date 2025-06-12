from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from typing import Dict


def build_pdf(graph_image: str, metrics: Dict[str, float], path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph('Telegram Chat Report', styles['Title']), Spacer(1, 12)]
    story.append(Image(graph_image, width=400, height=300))
    story.append(Spacer(1, 12))

    data = [['Metric', 'Value']]
    for key, value in metrics.items():
        data.append([key, value])

    table = Table(data, hAlign='LEFT')
    table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightblue]),
        ])
    )

    story.append(table)
    doc.build(story)

