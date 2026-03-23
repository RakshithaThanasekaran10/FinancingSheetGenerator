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

if __name__ == "__main__":
    agents = get_agents()
    print("Agents: ", agents[0])
    print()

    listings = get_listings()
    print("Listings:", listings[0])
    print()

    listing_agents = get_listing_agent()
    print("Listing Agents:", listing_agents[0])
    print()

    listing_open_houses = get_listing_open_house()
    print("Listing Open Houses:", listing_open_houses[0])
    print()

    organizations = get_organization()
    print("Organizations:", organizations[0])
    print()
    