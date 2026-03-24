import requests

# AGENT_URL = "https://xzkg-6hxh-f8to.n7d.xano.io/api:H1DGaTAQ/agent"

# def test_connection():
#     try:
#         response = requests.get(AGENT_URL)
#         response.raise_for_status
#         data = response.json()

#         print("Successfully Connected\n")
#         print("Sample Agent: ", data[0])
    
#     except Exception as e:
#         print("Error")
#         print(e)

# test_connection()

BASE_URL = "https://xzkg-6hxh-f8to.n7d.xano.io/api:H1DGaTAQ"

def get_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status
        return response.json()
    
    except Exception as e:
        print("Error Fetching /{endpoint}")
        print(e)
        return None
    
def get_agents():
    return get_data("agent")

def get_listings():
    return get_data("listing")

def get_listing_agent():
    return get_data("listing_agent")

def get_listing_open_house():
    return get_data("listing_open_house")

def get_organization():
    return get_data("organization")

# if __name__ == "__main__":
#     agents = get_agents()
#     print("Agents: ", agents[0])
#     print()

#     listings = get_listings()
#     print("Listings:", listings[0])
#     print()

#     listing_agents = get_listing_agent()
#     print("Listing Agents:", listing_agents[0])
#     print()

#     listing_open_houses = get_listing_open_house()
#     print("Listing Open Houses:", listing_open_houses[0])
#     print()

#     organizations = get_organization()
#     print("Organizations:", organizations[0])
#     print()

def get_property_address_from_mls(mls_number):
    """
    Given an MLS number, return the full property address.
    """
    listings = get_listings()

    for listing in listings:
        if str(listing.get("mls_number")) == str(mls_number):
            return(listing.get("property_address_full"))
    
    print(f"No listing found for MLS number {mls_number}")
    return None

def get_property_price_from_mls(mls_number):
    """
    Given an MLS number, return the property price (unformatted, e.g., 1000000 instead of 1,000,000).
    """
    listings = get_listings()

    for listing in listings:
        if str(listing.get("mls_number")) == str(mls_number):
            return listing.get("property_price_unformatted")
    
    print(f"No listing found for MLS number {mls_number}")
    return None

# TODO: Error handling for when there is no agent
# TODO: Error handling for when there are more than one agent for one listing
def get_agent_from_mls(mls_number):
    """
    Given an MLS number, return a dictionary of agent information for that listing.

    The dictionary includes:
    1. Name (Full Name)
    2. Position
    3. Phone
    4. Photo (As a URL)
    """
    listings = get_listings()
    listing_agents = get_listing_agent()
    agents = get_agents()

    listing_id = None
    for listing in listings:
        if str(listing.get("mls_number")) == str(mls_number):
            listing_id = listing.get("id")
    
    agent_id = None
    for listing_agent in listing_agents:
        if str(listing_agent.get("listing_id")) == str(listing_id):
            agent_id = listing_agent.get("agent_id")
        
    result = {}
    for agent in agents:
        if str(agent.get("id")) == str(agent_id):
            result["Name"] = agent.get("name")
            result["Position"] = agent.get("position")
            result["Phone"] = agent.get("agent_phone_primary")
            result["Photo"] = agent.get("photo_url")
            break
    
    return result
