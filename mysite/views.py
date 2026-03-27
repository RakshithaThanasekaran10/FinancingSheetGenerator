from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from requests import api
from weasyprint import HTML, CSS
from pathlib import Path
from django.conf import settings
from datetime import date
from mysite.utils import get_down_payment_scenarios, calculate_mortgage_summary
import base64
from .test_api import get_agents, get_listings, get_listing_agent, get_listing_open_house, get_organization
from django.core.cache import cache

def to_file_uri(path):
    return Path(path).resolve().as_uri()


def home(request):
    return render(request, "main/home.html")


def get_financing_data(mls_id, rate_percent, insurance_type):
    """Helper function to get financing data for PDF generation and AJAX preview
    -- should ret dict of all data for preview and pdf gen"""

     # Placeholder values (same as PDF generation)
    list_price, est_property_fees, est_condo_fees, est_heat_cost = 400000, 0, 0, 0
    list_address, agent_name, agent_phone, agent_id = "Unknown Address", "Unknown Agent", "Unknown Phone", ""

    # use cache to keep data from preview in case thats used before pdf gen 
    cache_key = f"fin_data_{mls_id}"
    cached_listing = cache.get(cache_key)

    if cached_listing:
        #print(f"--- DEBUG: Using cached data for MLS {mls_id} ---")
        listing = cached_listing
    else:
        #print(f"--- DEBUG: No cached data for MLS {mls_id}. Fetching from Xano... ---")
        listings = get_listings() or []
        listing = next((l for l in listings if str(l.get('mls_number')) == str(mls_id)), None)
        if listing:
            cache.set(cache_key, listing, timeout=300)  # Cache for 5 minutes
            #print(f"--- DEBUG: Caching data for MLS {mls_id} ---")
        
   
    rate = float(rate_percent or 0) / 100  # Convert percentage to decimal
    insurance_type = int(insurance_type or 0)

    if listing:
        #print(f"--- DEBUG: SUCCESS! Found price: {listing.get('property_price_unformatted')} ---")
        
        listing_agents = get_listing_agent() or []
        agents = get_agents() or []

        entry = next((a for a in listing_agents if a.get('listing_id') == listing.get('id')), None)
        agent = None
        if entry:
            agent = next((a for a in agents if a.get('id') == entry.get('agent_id')), None)

        list_address = listing.get('property_address_full', 'Unknown Address')

        if agent:
            agent_name = agent.get('name', 'Unknown Agent')
            agent_phone = agent.get('agent_phone_primary', 'Unknown Phone')
            agent_id = agent.get('position')
            agent_photo = agent.get('photo_url')
        else: 
            agent_name = "N/A"
            agent_phone = ""
            agent_id = ""
            agent_photo = None

        list_price = listing.get('property_price_unformatted', list_price)
        est_property_fees = listing.get('est_property_fees', est_property_fees)
        est_condo_fees = listing.get('est_condo_fees', est_condo_fees)
        est_heat_cost = listing.get('est_heat_cost', est_heat_cost)

    else:
        print(f"MLS ID {mls_id} not found in listings. Using default values.") 
        list_price, est_property_fees, est_condo_fees, est_heat_cost = 333333, 0, 0, 0

    # Down payment & mortgage calculations
    dp_scenarios = get_down_payment_scenarios(list_price)
    mortgage_scenarios = []
    for dp_percent in dp_scenarios:
        summary = calculate_mortgage_summary(
            list_price=list_price,
            down_payment_percentage=dp_percent,
            rate=rate,  # Convert percentage to decimal
            est_property_fees=est_property_fees,
            est_condo_fees=est_condo_fees,
            est_heat_cost=est_heat_cost,
            insurance_type=insurance_type
        )
        mortgage_scenarios.append(summary)

    return {
        "property_info": {
            "address": list_address,
            "agent_name": agent_name,
            "agent_phone": agent_phone,
            "agent_id": agent_id,
            "agent_photo": agent_photo,
        },
        "list_price": list_price,
        "dp_scenarios": dp_scenarios,
        "mortgage_scenarios": mortgage_scenarios,
        "rate": rate * 100,  # Convert back to percentage for display
        "insurance_type": insurance_type
    }

def get_preview_data(request):
    """AJAX endpoint to get preview data for live calculations"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Get parameters from query string
        data = get_financing_data(
            request.GET.get("mls", ""),
            request.GET.get("rate", "0"),
            request.GET.get("insurance_type", "0")
        )
        return JsonResponse(data)
    except (ValueError, TypeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


def generate_pdf(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)

    mls_id = request.POST.get("mls", "")
    rate = float(request.POST.get("rate", 0)) / 100  # Convert percentage to decimal
    insurance_type = int(request.POST.get("insurance_type", 0))
    property_pic = request.FILES.get("property_pic")

    rate_from_post = request.POST.get("rate", "0")
    fin_data = get_financing_data(mls_id, float(rate_from_post), insurance_type)  # Pass rate as percentage for display

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
        "property_info": fin_data["property_info"],
        "rate": fin_data["rate"],  # Convert back to percentage for display
        "insurance_type": insurance_type,
        "list_price": fin_data["list_price"],
        "dp_scenarios": fin_data["dp_scenarios"],
        "mortgage_scenarios": fin_data["mortgage_scenarios"],
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
