from s1_api import S1Api
import copy

""""Modifies the site to be compatible with the destination account and site creation."""
def adapt_site(site, dest_account_id):
    new_site = copy.deepcopy(site)
    new_site["accountId"] = dest_account_id
    del new_site.get("licenses")["settings"]
    for key in ["expiration", "createdAt", "id", "creatorId", "updatedAt", "creator", "sku", "suite", "registrationToken", "accountName"]:
        del new_site[key]
    return {"data": new_site}

""""Modifies the group to be compatible with the destination account and site creation."""
def adapt_group(group, dest_account_id, dest_site_id):
    new_group = copy.deepcopy(group)
    new_group["accountId"] = dest_account_id
    new_group["siteId"] = dest_site_id
    for key in ['accountId', 'createdAt', 'id', 'filterName', 'creatorId', 'registrationToken', 
                'totalAgents', 'updatedAt', 'creator']:
        del new_group[key]
    return {"data" : new_group}    

def migrate_structure(origin_API, dest_API, origin_account_id, dest_account_id):
    sites = origin_API.get_sites(origin_account_id)
    for site in sites:
        dest_site = adapt_site(site, dest_account_id)
        dest_site_id = dest_API.create_site(dest_site)
        groups = origin_API.get_groups(origin_account_id, site.get("id"))
        for group in groups:
            if group.get("name") == "Default Group":
                continue
            if group.get("inherits") == False:
                group["policy"] = origin_API.get_group_policy(group.get("id"))
            dest_group = adapt_group(group, dest_account_id, dest_site_id)
            dest_group_id = dest_API.create_group(dest_group)
