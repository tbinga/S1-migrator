import requests

def delete_addon(site, addon_name):
    for entry in site.get("data").get("licenses").get("modules"):
        if entry.get("name") == addon_name:
            site.get("data").get("licenses").get("modules").remove(entry)
    return site


class S1Api:

    def __init__(self, base_url, auth_header):
        self.base_url = base_url
        self.auth_header = auth_header
        self.remove_rogues = False

    #Funcion to get all of the REST Ressource from url (Makes multiple requests if totalItems > limit)
    def _get_all(self, url, limit):
        first_part = requests.get(f"{url}&limit={limit}", headers=self.auth_header).json()
        if "nextCursor" in first_part["pagination"]:
            data = first_part["data"]
            next_cursor = first_part["pagination"]["nextCursor"]
            while next_cursor is not None:
                next_part = requests.get(f"{url}&limit={limit}&cursor={next_cursor}", headers=self.auth_header).json()
                if "nextCursor" in next_part["pagination"]:     
                    next_cursor = next_part["pagination"]["nextCursor"]
                else:
                    next_cursor = None
                data.extend(next_part["data"])
        else:
            return first_part["data"]
        return data

    # Returns all exclusion from a specific account_id 
    def get_exclusions(self, account_id):
        return self._get_all(f"{self.base_url}exclusions?accountIds={account_id}&includeChildren=true&sortBy=scopePath", 1000)

    def create_exclusion(self, exclusion):
        response = requests.post(f"{self.base_url}exclusions", json=exclusion, headers=self.auth_header)
        if response.status_code == 200:
            #print(f"exclusion {exclusion.get('name')} successfully created")
            return [response.json()["data"][i]["id"] for i in range(len(response.json()["data"]))] #Returns the list of exclusion ids created (should be only one)
        else:
            raise Exception(response.json(), exclusion)

    def get_sites(self, account_id):
        return self._get_all(f"{self.base_url}sites?accountId={account_id}&siteType=Paid", 200).get("sites")

    def get_groups(self, account_id, site_id):
        return self._get_all(f"{self.base_url}groups?accountIds={account_id}&siteIds={site_id}", 200)

    def create_site(self, site):
        if self.remove_rogues:
            site = delete_addon(site, "rogues")

        response = requests.post(f"{self.base_url}sites", json=site, headers=self.auth_header)

        if response.status_code == 200:
            name = response.json().get("data").get("name")
            print(f"site {name} successfully created")
            return response.json().get("data").get("id")
        
        elif "rogues Add-on is not available in this scope" in str(response.content):
            site_name = site.get("data").get('name')
            print(f"rogues Add-on is not available in this scope for site {site_name}")
            print("Do you want to remove the rogues Add-on from this site and the next ones? (y/n)")
            answer = input()
            if answer == "y" or answer == "Y":
                self.remove_rogues = True
                delete_addon(site, "rogues")
            else:
                return None
        else:
            raise Exception(response.json(), site)
        
    def create_group(self, group):
        response = requests.post(f"{self.base_url}groups", json=group, headers=self.auth_header)
        if response.status_code == 200:
            name = response.json().get("data").get("name")
            print(f"    group {name} successfully created")
            return response.json().get("data").get("id")
        else:
            raise Exception(response.json(), group)
        
    def get_group_policy(self, group_id):
        response = requests.get(f"{self.base_url}groups/{group_id}/policy", headers=self.auth_header)
        if response.status_code == 200:
            return response.json().get("data")
        else:
            raise Exception(response.json(), group_id)