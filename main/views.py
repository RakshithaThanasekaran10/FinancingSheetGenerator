from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

def home(request):
    """
    Homepage view: renders the skeleton of the finance sheet generator
    """
    return render(request, "main/home.html") 

def generate_pdf(request):

    if request.method == "POST":

        income = float(request.POST.get("income", 0))
        expenses = float(request.POST.get("expenses", 0))
        balance = income - expenses

        html_string = render_to_string(
            "pdf_template.html",
            {
                "income": income,
                "expenses": expenses,
                "balance": balance
            }
        )

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=finance_sheet.pdf"

        return response