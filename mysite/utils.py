# Calculates mortgage payment (PMT) 
def pmt(rate, number_of_periods, present_value):
    ### monthly_rate = 0.05 / 12
    ## does this need to be changed to 0.1666667 --> 1/6??
    monthly_rate = (((rate / 2) + 1) ** (1/6)) - 1

    # handling 0% interest rate case
    if monthly_rate == 0:
        return present_value / number_of_periods
    
    # The Standard Annuity Formula (PMT) = Payment = [P * r] / [1 - (1 + r)^-n]
    num = present_value * monthly_rate
    denom = 1 - ((1 + monthly_rate)**-number_of_periods)
    #payment = round(num / denom, 2)
    return num/denom

def cmhc_premium_rate(dp_percent: float) -> float:
    #Premium rate based on down payment percent (H13)
    if dp_percent < 10:
        return 0.04
    if dp_percent < 15:
        return 0.031
    if dp_percent < 20:
        return 0.028
    return 0.0
    
def calc_mortgage_insurance_fee(purchase_price: float, down_payment_percent: float, insurance_type: int) -> float:
    # DP >= 20 = no insurance 
    # OR ++ unsured 30 year amortization
    if down_payment_percent >= 20 or insurance_type == 2:
        return 0.0
    
    mortgage_amount = purchase_price * (1 - down_payment_percent / 100.0)
    base = mortgage_amount * cmhc_premium_rate(down_payment_percent)
    
    if insurance_type == 1:
        # surcharge = for premium?
        surcharge = (mortgage_amount * (1 - down_payment_percent / 100.0)) * 0.002
        return base + surcharge
        
    if insurance_type == 0:
        return base
        
    return 0.0


def calculate_mortgage_summary(list_price, down_payment_percentage, rate, est_property_fees, est_condo_fees, est_heat_cost, insurance_type):
    # get legal down payment
    legal_down_payment = get_min_down_payment(list_price)
    down_payment = list_price * (down_payment_percentage / 100.0)
    down_payment = max(down_payment, legal_down_payment) 
    
    mortgage_amount = list_price - down_payment
    # insurance_type can be 0 or 1 based on user selection
    actual_dp_percent = (down_payment / list_price) * 100
    mortgage_insurance_fee = calc_mortgage_insurance_fee(list_price, actual_dp_percent, insurance_type)  
    total_mortgage_insurance = mortgage_amount + mortgage_insurance_fee 

    # present_value = total_mortgage_insurance
        
    # insured, insurable = 25 years, uninsured = 30 years
    #amortization_years = 25 if insurance_type in [0, 1] else 30
    if insurance_type in [0, 1]:
        amortization_years = 25
    elif insurance_type == 2:
        amortization_years = 30
    else: 
        amortization_years = 30 if actual_dp_percent >= 20 else 25

    number_of_periods = amortization_years * 12

    monthly_mortgage = pmt(rate, number_of_periods, total_mortgage_insurance)
    rounded_monthly_mortgage = round(monthly_mortgage)

    biweekly_payment = (monthly_mortgage * 12) / 26

    total_monthly_payment = monthly_mortgage + est_property_fees + est_condo_fees + est_heat_cost
    rounded_total_monthly_payment = round(total_monthly_payment)
    annual_gross_income_required = round((rounded_total_monthly_payment * 12) / 0.32)

    return {
        "down_payment": down_payment,
        "mortgage_amount": mortgage_amount,
        "mortgage_insurance_fee": mortgage_insurance_fee,
        "total_mortgage_insurance": total_mortgage_insurance,
        "monthly_mortgage": rounded_monthly_mortgage,
        "biweekly_payment": round(biweekly_payment),
        "total_monthly_payment": total_monthly_payment,
        "annual_gross_income_required": annual_gross_income_required
    }


def get_down_payment_scenarios(list_price): 
    if list_price < 500000:
        return [5.0, 10.0, 20.0]
    elif list_price <= 750000:
        return [10.0, 15.0, 20.0]
    elif list_price <= 1000000:
        return [15.0, 20.0, 35.0]
    return [20.0, 35.0, 50.0]


def get_min_down_payment(list_price):
    if list_price < 500000:
        return list_price * 0.05
    elif list_price < 1500000:
        return (500000 * 0.05) + ((list_price - 500000) * 0.10)
    return list_price * 0.2


## Testing
### CODE BELOW ALL GENERATED WITH AI
def print_comparison_table(list_price, dp_percentages, rate, prop_fees, condo_fees, heat_cost, insurance_type):
    # Header logic
    headers = [f"{dp}%" for dp in dp_percentages]
    col_width = 18
    first_col_width = 35
    total_width = first_col_width + (col_width * len(headers))

    # Title and Rate
    print(f"\n{'Based on an Insured Rate of*':>{total_width}}")
    print(f"{f'{rate*100:.2f}%':>{total_width}}")
    print("-" * total_width)

    # Column Headers
    header_row = f"{'':<{first_col_width}}" + "".join([f"{h:>{col_width}}" for h in headers])
    print(header_row)
    print("-" * total_width)

    # Calculate data for each column
    summaries = [calculate_mortgage_summary(list_price, dp, rate, prop_fees, condo_fees, heat_cost, insurance_type) for dp in dp_percentages]

    # Row definitions: (Label, key_in_summary_dict)
    rows = [
        ("List Price:", None, list_price),
        ("Down Payment:", "down_payment", None),
        ("Mortgage Amount:", "mortgage_amount", None),
        ("Mortgage Insurance Fee:", "mortgage_insurance_fee", None),
        ("Total Mortgage & Insurance Fee:", "total_mortgage_insurance", None),
        ("", None, None), # Spacer
        ("Mortgage Payment:", "monthly_mortgage", None),
        ("Estimated Property Taxes:", None, prop_fees),
        ("Estimated Condo Fees:", None, condo_fees),
        ("Estimated Heat Cost:", None, heat_cost),
        ("Est Total Monthly Shelter Expense:", "total_monthly_payment", None),
        ("Est Annual Gross Income Required:", "annual_gross_income_required", None)
    ]

    for label, key, static_val in rows:
        if label == "":
            print("-" * total_width)
            continue
            
        row_str = f"{label:<{first_col_width}}"
        for summary in summaries:
            val = static_val if static_val is not None else summary[key]
            row_str += f"${val:>{col_width-1},.0f}" # .0f to match your image's rounding
        
        # Highlight the final row
        if "Annual Gross Income" in label:
            print("=" * total_width)
            print(row_str)
            print("=" * total_width)
        else:
            print(row_str)

"""
# --- EXECUTION ---

# Given values -- these would be imported from API

down_payment_percentage = 20.0      # input as percentage, e.g., 20 for 20%
list_price = 400000
est_property_fees = 426
est_condo_fees = 0
est_heat_cost = 100
rate = 0.0459     # annual interest rate, converted to monthly in the pmt function

dp_scenarios = get_down_payment_scenarios(list_price)

print_comparison_table(
    list_price=400000,
    dp_percentages=dp_scenarios,
    rate=0.0459,
    prop_fees=426,
    condo_fees=0,
    heat_cost=100,
    insurance_type=0
)
"""