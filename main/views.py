from django.shortcuts import render
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io


def home(request):
    income = 0
    expenses = 0
    balance = 0
    rate = 0
    mls = ""

    if request.method == "POST":
        try:
            income = float(request.POST.get("income", 0))
            expenses = float(request.POST.get("expenses", 0))
            rate = float(request.POST.get("rate", 0))
            mls = request.POST.get("mls", "")

            balance = income - expenses

            # --------- PDF GENERATION ----------
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            styles = getSampleStyleSheet()

            elements.append(Paragraph("<b>Financing Sheet</b>", styles["Title"]))
            elements.append(Spacer(1, 0.3 * inch))

            elements.append(Paragraph(f"MLS Number: {mls}", styles["Normal"]))
            elements.append(Paragraph(f"Mortgage Rate: {rate}%", styles["Normal"]))
            elements.append(Spacer(1, 0.3 * inch))

            elements.append(Paragraph(f"Monthly Income: ${income}", styles["Normal"]))
            elements.append(Paragraph(f"Monthly Expenses: ${expenses}", styles["Normal"]))
            elements.append(Paragraph(f"Remaining Balance: ${balance}", styles["Normal"]))

            doc.build(elements)

            buffer.seek(0)

            return HttpResponse(
                buffer,
                content_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="financing_sheet_{mls}.pdf"'
                },
            )

        except ValueError:
            pass

    context = {
        "income": income,
        "expenses": expenses,
        "balance": balance,
    }

    return render(request, "main/home.html", context)