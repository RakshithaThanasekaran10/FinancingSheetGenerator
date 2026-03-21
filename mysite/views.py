from django.shortcuts import render
from django.http import HttpResponse
#from django.template.loader import render_to_string
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from datetime import date

def home(request):
    """
    Homepage view: renders the skeleton of the finance sheet generator
    """
    return render(request, "main/home.html")

def link_callback(uri, rel):
    if uri.startswith('/static/'):
        path = os.path.join(settings.BASE_DIR, 'main', 'static', uri.replace('/static/', ''))
    else:
        return uri

    if not os.path.isfile(path):
        raise Exception(f'Image not found: {path}')

    return path

def generate_pdf(request):
    if request.method == "POST":

        income = float(request.POST.get("income", 0))
        expenses = float(request.POST.get("expenses", 0))
        balance = income - expenses

        # Load template
        template = get_template("main/pdf_template.html")

        # Build absolute paths for CSS and images
        css_path = os.path.join(settings.BASE_DIR, 'static', 'pdf_design.css')
        images = {
            "kelly": "/static/img/1.png",
            "qrcode": "/static/img/qr_code.png",
            "brx": "/static/img/Copy of BRX Logo_ON_Black Transparent.png",
            "HaickLogo": "/static/img/Copy of recent logo.png",
        }

        # Prepare context
        context = {
            "income": income,
            "expenses": expenses,
            "balance": balance,
            "css_path": css_path,
            "images": images,
            "current_date": date.today(),
        }

        # Render HTML
        html = template.render(context)

        # Generate PDF
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=finance_sheet.pdf"

        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            link_callback=link_callback  # THIS FIXES IMAGES
        )

        if pisa_status.err:
            return HttpResponse("Error generating PDF")

        return response