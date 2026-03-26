from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML, CSS
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from datetime import date
from mysite.utils import get_down_payment_scenarios, calculate_mortgage_summary

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

        mls_id = request.POST.get("mls", "")
        rate = float(request.POST.get("rate", 0)) / 100  # Convert percentage to decimal
        insurance_type = int(request.POST.get("insurance_type", 0))
        property_pic = request.FILES.get("property_pic")

        # TODO: These will come from API integration
        list_price = 400000  # Placeholder
        est_property_fees = 426  # Placeholder
        est_condo_fees = 0  # Placeholder
        est_heat_cost = 100  # Placeholder

        # Get down payment scenarios and calculate mortgages
        dp_scenarios = get_down_payment_scenarios(list_price)
        mortgage_scenarios = []
        for dp_percent in dp_scenarios:
            summary = calculate_mortgage_summary(
                list_price=list_price,
                down_payment_percentage=dp_percent,
                rate=rate,
                est_property_fees=est_property_fees,
                est_condo_fees=est_condo_fees,
                est_heat_cost=est_heat_cost,
                insurance_type=insurance_type
            )
            mortgage_scenarios.append(summary)

        # try to inline upload pic for pdf if possible; will fallback to static if not.
        uploaded_pic_data = None
        if property_pic:
            try:
                import base64
                uploaded_pic_data = "data:%s;base64,%s" % (
                    property_pic.content_type,
                    base64.b64encode(property_pic.read()).decode('utf-8')
                )
            except Exception:
                uploaded_pic_data = None

        template = get_template("main/pdf_template.html")

        css_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'pdf_design.css')
        images = {
            "kelly": "/static/img/1.png",
            "qrcode": "/static/img/qr_code.png",
            "brx": "/static/img/Copy of BRX Logo_ON_Black Transparent.png",
            "HaickLogo": "/static/img/Copy of recent logo.png",
            "defaultAgent": "/static/img/default.png",
        }

        context = {
            "mls_id": mls_id,
            "rate": rate * 100,  # Convert back to percentage for display
            "insurance_type": insurance_type,
            "list_price": list_price,
            "dp_scenarios": dp_scenarios,
            "mortgage_scenarios": mortgage_scenarios,
            "uploaded_pic_data": uploaded_pic_data,
            "css_path": css_path,
            "images": images,
            "current_date": date.today(),
        }

        html_string = template.render(context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=finance_sheet.pdf"

        # Use WeasyPrint instead of xhtml2pdf
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(
            response, stylesheets=[CSS(css_path)]
        )

        return response

    return HttpResponse("Invalid request", status=400)
