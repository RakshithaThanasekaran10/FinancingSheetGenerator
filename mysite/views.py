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

        mls_id = request.POST.get("mls", "")
        rate = float(request.POST.get("rate", 0))
        insurance_type = int(request.POST.get("insurance_type", 0))
        property_pic = request.FILES.get("property_pic")

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

        # computation: convert rate to monthly rate as a derived value
        monthly_rate = rate / 100 / 12

        template = get_template("main/pdf_template.html")

        css_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'pdf_design.css')
        images = {
            "kelly": "/static/img/1.png",
            "qrcode": "/static/img/qr_code.png",
            "brx": "/static/img/Copy of BRX Logo_ON_Black Transparent.png",
            "HaickLogo": "/static/img/Copy of recent logo.png",
        }

        context = {
            "mls_id": mls_id,
            "rate": rate,
            "monthly_rate": monthly_rate,
            "insurance_type": insurance_type,
            "uploaded_pic_data": uploaded_pic_data,
            "css_path": css_path,
            "images": images,
            "current_date": date.today(),
        }

        html = template.render(context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=finance_sheet.pdf"

        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            link_callback=link_callback
        )

        if pisa_status.err:
            return HttpResponse("Error generating PDF")

        return response

    return HttpResponse("Invalid request", status=400)