import requests
from s1_api import get_sites, get_groups, get_exclusions
convert_ids = lambda ids, map: [str(map[id]) for id in ids]


def get_name_to_id_map(sites):
    returned_map = dict()
    for site in sites:
        returned_map[site["name"]] = site["id"]
    return returned_map

"""Parses exclusion data from GET request, returns data for the the POST payload."""
def parse_exclusion_data(exclusion_data):
    siteIds, groupIds = [], []

    if exclusion_data["scopeName"] == "site":
        siteIds = exclusion_data["scope"]["siteIds"]
    if exclusion_data["scopeName"] == "group":
        groupIds = exclusion_data["scope"]["groupIds"]
    
    exclusion_type = exclusion_data.get("type")
    actions = [] if exclusion_data.get("actions") == None else exclusion_data.get("actions")
    new_data = {
    "mode": exclusion_data.get("mode"),
    "type": exclusion_type,
    "value": exclusion_data.get("value"),
    "description": exclusion_data.get("description"),
    "source": exclusion_data.get("source"),
    "pathExclusionType": exclusion_data.get("pathExclusionType"),
    "actions": actions,
    "osType": exclusion_data.get("osType"),
    #"inject": True #Deprecated 
}
    if exclusion_type != "path":
        del new_data["pathExclusionType"]
    return groupIds, siteIds, new_data

"""Exclusion data must be in this form: 
"""
def create_exclusion(base_url, auth_header, exclusion_data, account_id, site_map, group_map):
    url = base_url + "exclusions"
    filter={}
    group_ids, site_ids, formatted_data = parse_exclusion_data(exclusion_data)
    
    if group_ids: #Group exclusion
        filter = {
    "groupIds": convert_ids(group_ids, group_map),
    "tenant": "true"
        }
    elif site_ids: #Site exclusion
        filter = {
    "siteIds": convert_ids(site_ids, site_map),
    "tenant": "true"
        }
    else : #Account exclusion
        filter = {
    "accountIds": [str(account_id)],
    "tenant": "true"
        }

    post_data = {"filter": filter, "data": formatted_data}
    response = requests.post(url=url, json=post_data, headers=auth_header)
    if response.status_code == 200:
        print(f"exclusion successfully created")
        return [response.json()["data"][i]["id"] for i in range(len(response.json()["data"]))] #Returns the list of exclusion ids created (should be only one)
    else:
        raise Exception(response.json(), post_data)

"""Returns two dictionnaries that maps group_ids and site_ids from origin to destination console.
Both accounts must have the same sites and groups (same names)
""" 
def get_id_maps(origin_url, dest_url, origin_account_id, dest_account_id, origin_auth_header, dest_auth_header):

    group_id_map, site_id_map = dict(), dict()
    

    origin_sites = get_sites(origin_url, origin_account_id, origin_auth_header)
    origin_site_names_to_id = get_name_to_id_map(origin_sites)

    dest_sites = get_sites(dest_url, dest_account_id, dest_auth_header)
    dest_sites_name_to_id = get_name_to_id_map(dest_sites)


    for (origin_site_name, origin_site_id) in origin_site_names_to_id.items():
        if origin_site_name in dest_sites_name_to_id.keys():
            dest_site_id = dest_sites_name_to_id[origin_site_name]
            site_id_map[origin_site_id] = dest_site_id

            origin_groups = get_groups(origin_url, origin_account_id, origin_site_id, origin_auth_header)
            origin_groups_names_to_id = get_name_to_id_map(origin_groups)

            dest_groups = get_groups(dest_url, dest_account_id, dest_site_id, dest_auth_header)
            dest_groups_name_to_id = get_name_to_id_map(dest_groups)

            for (origin_group_name, origin_group_id) in origin_groups_names_to_id.items():
                if origin_group_name in dest_groups_name_to_id.keys():
                    dest_group_id = dest_groups_name_to_id[origin_group_name]
                    group_id_map[origin_group_id] = dest_group_id
                else : 
                    print(f"{origin_site_name}/{origin_group_name} not present on destination account")
        else:
            print(f"site {origin_site_name} not present on destination account")

    return group_id_map, site_id_map
        



    #for original_site in original_sites:
        #if original_site.name

"""Migrates the exclusions from the origin account to the destination account"""
def migrate_exclusions(origin_url, dest_url, origin_account_id, dest_account_id, origin_auth_header, dest_auth_header):
    #Get all exclusions
    exclusions = get_exclusions(origin_url, origin_account_id, origin_auth_header)
    count=len(exclusions)
    print(f"Retrieved {count} exclusions")
    group_id_map, site_id_map = get_id_maps(origin_url, dest_url, origin_account_id, dest_account_id, origin_auth_header, dest_auth_header)
    print(f"Retrieved mapped Group and Site Ids")
    created_exclusions = []
    i=0

    for exclusion in exclusions:
        errors_list = []
        post_data={}
        try:
            ids = []
            ids = create_exclusion(dest_url, dest_auth_header, exclusion, dest_account_id, site_id_map, group_id_map)
            created_exclusions.extend(ids)
            print(f"Id of created exclusion: {ids}")
            i+=1
        except Exception as e:
            title = e.args[0]["errors"][0]["title"]
            post_data = e.args[1]
            if title != "Already Exists Error" :
                print(f"Error: {e}")
                print(f"inExclusion: {exclusion}, outExclusion: {post_data}")
            errors_list.append(e)
        
        #print(f"{i}/{count} treated")
    print(f"Job finished. \nNew exclusions ids: {created_exclusions}")
    print(f"Errors: {errors_list}")
