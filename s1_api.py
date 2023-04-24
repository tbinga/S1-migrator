import requests

#Funcion to get all of the REST Ressource from url (Makes multiple requests if totalItems > limit)
def get_all(url, auth_header, limit):
    first_part = requests.get(f"{url}&limit={limit}", headers=auth_header).json()
    if "nextCursor" in first_part["pagination"]:
        data = first_part["data"]
        next_cursor = first_part["pagination"]["nextCursor"]
        while next_cursor is not None:
            next_part = requests.get(f"{url}&limit={limit}&cursor={next_cursor}", headers=auth_header).json()
            if "nextCursor" in next_part["pagination"]:     
                next_cursor = next_part["pagination"]["nextCursor"]
            else:
                next_cursor = None
            data.extend(next_part["data"])
    else:
        return first_part["data"]
    return data

# Returns all exclusion from a specific account_id 
def get_exclusions(base_url, account_id, auth_header):
    return get_all(f"{base_url}exclusions?accountIds={account_id}&includeChildren=true&sortBy=scopePath", auth_header, 1000)

def get_sites(url, account_id, authHeader):
    response = get_all(f"{url}sites?accountId={account_id}&siteType=Paid", authHeader, 200)
    return response.get("sites")

def get_groups(url, account_id, site_id, authHeader):
    response = get_all(f"{url}groups?accountIds={account_id}&siteIds={site_id}", authHeader, 200)
    return response

def create_site(url, authHeader, site):
    response = requests.post(f"{url}sites", json=site, headers=authHeader)
    if response.status_code == 200:
        name = response.json().get("data").get("name")
        print(f"site {name} successfully created")
        return response.json().get("data").get("id")
    else:
        raise Exception(response.json(), site)
    
def create_group(url, authHeader, group):
    response = requests.post(f"{url}groups", json=group, headers=authHeader)
    if response.status_code == 200:
        name = response.json().get("data").get("name")
        print(f"    group {name} successfully created")
        return response.json().get("data").get("id")
    else:
        raise Exception(response.json(), group)
    
def get_group_policy(url, authHeader, group_id):
    response = requests.get(f"{url}groups/{group_id}/policy", headers=authHeader)
    if response.status_code == 200:
        return response.json().get("data")
    else:
        raise Exception(response.json(), group_id)