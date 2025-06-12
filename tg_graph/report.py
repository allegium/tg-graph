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
from typing import Dict, List, Tuple


def _format_metrics(metrics: Dict[str, float]) -> List[List[str]]:
    """Convert metrics to a structured table with categories in Russian."""

    rows: List[List[str]] = [["Категория", "Метрика", "Значение"]]

    overview = [
        ("число узлов", metrics.get("nodes", 0)),
        ("число рёбер", metrics.get("edges", 0)),
        ("средняя степень", f"{metrics.get('avg_degree', 0):.2f}"),
        ("кластеры", metrics.get("clusters", 0)),
        ("диаметр", metrics.get("diameter", 0)),
    ]
    for name, value in overview:
        rows.append(["Общее", name, value])

    return rows


def build_pdf(
    graph_image: str,
    metrics: Dict[str, float],
    strengths: Dict[Tuple[str, str], float],
    path: str,
) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("Отчёт по чату Telegram", styles["Title"]), Spacer(1, 12)]
    # Slightly larger graph image for better readability in the PDF
    story.append(Image(graph_image, width=500, height=380, kind="proportional"))
    story.append(Spacer(1, 12))

    data = _format_metrics(metrics)

    table = Table(data, hAlign="LEFT", colWidths=[80, 200, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.beige, colors.lightblue]),
            ]
        )
    )

    story.append(table)

    # Connection strengths table
    if strengths:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Сила связей", styles["Heading2"]))
        rows = [["От", "Кому", "Сила"]]
        for (src, dst), val in sorted(strengths.items(), key=lambda x: x[1], reverse=True):
            rows.append([src, dst, f"{val:.2f}"])
        s_table = Table(rows, hAlign="LEFT", colWidths=[150, 150, 80])
        s_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.beige, colors.lightblue]),
                ]
            )
        )
        story.append(s_table)
    doc.build(story)

