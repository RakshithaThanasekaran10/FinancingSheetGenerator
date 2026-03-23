from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from datetime import date
from mysite.utils import get_down_payment_scenarios, calculate_mortgage_summary

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io
from .test_api import get_agents, get_listings, get_listing_agent

def home(request):
    """
    Homepage view: renders the skeleton of the finance sheet generator
    """
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
                    "Content-Disposition": f'attachment; filename="financingsheet{mls}.pdf"'
                },
            )

        except ValueError:
            pass

    context = {
        "income": income,
        "expenses": expenses,
        "balance": balance,
    }


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
    print("---- GENERATE PDF CALLED ----")
    if request.method == "POST":

        user_mls = request.POST.get("mls", "").strip()
        rate = float(request.POST.get("rate", 0)) / 100  # Convert percentage to decimal
        insurance_type = int(request.POST.get("insurance_type", 0))
        property_pic = request.FILES.get("property_pic")

        #connect api with agent information, MLS number, and property address
        agents = get_agents()
        listings = get_listings()
        listing_agents = get_listing_agent()

        #takes MLS number

        #test
        print("User entered MLS:", user_mls)
        print("Available MLS in API:", [str(l.get("mls_number")) for l in listings])

        #grab listing number
        listing = next(
            (l for l in listings if str(l.get("mls_number")).strip() == user_mls),
            None
        )
        if not listing:
            return HttpResponse("Listing not found")

        # find matching agent
        agent_id = None
        for la in listing_agents:
            if la["listing_id"] == listing["id"]:
                agent_id = la["agent_id"]
                break

        agent = next((a for a in agents if a["id"] == agent_id), None)

        property_address = listing.get("address", "N/A")
        mls_id = listing.get("mls_number", "N/A")

        agent_name = agent.get("name", "N/A") if agent else "N/A"
        agent_phone = agent.get("phone", "N/A") if agent else "N/A"

        #test
        print("MLS entered:", mls_id)
        print("Listing found:", listing)
        print("Agent found:", agent)

        # Get values from API listing
        list_price = listing.get("property_price_unformatted", 400000)
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
            "defaultHouse": "/static/img/PropertyPlaceholder.png",
        }

        context = {
            "mls_id": mls_id,
            "property_address": property_address,
            "agent_name": agent_name,
            "agent_phone": agent_phone,

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