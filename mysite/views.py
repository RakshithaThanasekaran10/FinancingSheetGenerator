from django.shortcuts import render
from django.http import HttpResponse
#from django.template.loader import render_to_string
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings

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

        # Load template
        template = get_template("main/pdf_template.html")

        # 1️⃣ Build absolute paths for CSS and images
        css_path = os.path.join(settings.BASE_DIR, 'static', 'pdf_design.css')
        images = {
            "one": os.path.join(settings.BASE_DIR, 'main', 'static', 'img', '1.png'),
            # "agent_johnny": os.path.join(settings.BASE_DIR, 'main', 'static', 'img', 'johnny.png'),
            # "agent_kelly": os.path.join(settings.BASE_DIR, 'main', 'static', 'img', 'kelly.png'),
        } # adjust filename if needed

        # 2️⃣ Prepare context
        context = {
            "income": income,
            "expenses": expenses,
            "balance": balance,
            "css_path": css_path,
            "img_path": images,
        }

        # Render HTML
        html = template.render(context)

        # 3️⃣ Generate PDF
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=finance_sheet.pdf"

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse("Error generating PDF")

        return response