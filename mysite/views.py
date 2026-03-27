from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from weasyprint import HTML, CSS
from pathlib import Path
from django.conf import settings
from datetime import date
from mysite.utils import get_down_payment_scenarios, calculate_mortgage_summary
import base64



def to_file_uri(path):
    return Path(path).resolve().as_uri()


def home(request):
    return render(request, "main/home.html")


def get_preview_data(request):
    """AJAX endpoint to get preview data for live calculations"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Get parameters from query string
        rate = float(request.GET.get("rate", 0)) / 100  # Convert percentage to decimal
        insurance_type = int(request.GET.get("insurance_type", 0))

        # Placeholder values (same as PDF generation)
        list_price = 400000
        est_property_fees = 426
        est_condo_fees = 0
        est_heat_cost = 100

        # Down payment & mortgage calculations
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

        return JsonResponse({
            "list_price": list_price,
            "dp_scenarios": dp_scenarios,
            "mortgage_scenarios": mortgage_scenarios,
            "rate": rate * 100,  # Convert back to percentage for display
            "insurance_type": insurance_type
        })

    except (ValueError, TypeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


def generate_pdf(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)

    mls_id = request.POST.get("mls", "")
    rate = float(request.POST.get("rate", 0)) / 100  # Convert percentage to decimal
    insurance_type = int(request.POST.get("insurance_type", 0))
    property_pic = request.FILES.get("property_pic")

    # Placeholder values
    list_price = 400000
    est_property_fees = 426
    est_condo_fees = 0
    est_heat_cost = 100

    # Down payment & mortgage calculations
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

    # Inline uploaded property picture
    uploaded_pic_data = None
    if property_pic:
        try:
            uploaded_pic_data = "data:%s;base64,%s" % (
                property_pic.content_type,
                base64.b64encode(property_pic.read()).decode('utf-8')
            )
        except Exception:
            uploaded_pic_data = None

    # Absolute paths to static images for WeasyPrint (as file:// URIs)
    static_img_path = Path(settings.BASE_DIR) / 'main' / 'static' / 'img'
    images = {
        "kelly": to_file_uri(static_img_path / '1.png'),
        "qrcode": to_file_uri(static_img_path / 'qr_code.png'),
        "brx": to_file_uri(static_img_path / 'Copy of BRX Logo_ON_Black Transparent.png'),
        "HaickLogo": to_file_uri(static_img_path / 'Copy of recent logo.png'),
        "defaultAgent": to_file_uri(static_img_path / 'default.png'),
    }

    template = get_template("main/pdf_template.html")
    css_path = str(Path(settings.BASE_DIR) / 'main' / 'static' / 'pdf_design.css')

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

    # Use WeasyPrint to render PDF
    HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(
        response, stylesheets=[CSS(css_path)]
    )

    return response
