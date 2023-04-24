import requests
from s1_api import S1Api
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
def create_exclusion(dest_API, exclusion_data, account_id, site_map, group_map):
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
    return dest_API.create_exclusion(post_data)

"""Returns two dictionnaries that maps group_ids and site_ids from origin to destination console.
Both accounts must have the same sites and groups (same names)
""" 
def get_id_maps(origin_API, dest_API, origin_account_id, dest_account_id):

    group_id_map, site_id_map = dict(), dict()

    

    origin_sites = origin_API.get_sites(origin_account_id)
    origin_site_names_to_id = get_name_to_id_map(origin_sites)

    dest_sites = dest_API.get_sites(dest_account_id)
    dest_sites_name_to_id = get_name_to_id_map(dest_sites)


    for (origin_site_name, origin_site_id) in origin_site_names_to_id.items():
        if origin_site_name in dest_sites_name_to_id.keys():
            dest_site_id = dest_sites_name_to_id[origin_site_name]
            site_id_map[origin_site_id] = dest_site_id

            origin_groups = origin_API.get_groups(origin_account_id, origin_site_id)
            origin_groups_names_to_id = get_name_to_id_map(origin_groups)

            dest_groups = dest_API.get_groups(dest_account_id, dest_site_id)
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
def migrate_exclusions(origin_API, dest_API, origin_account_id, dest_account_id):
    #Get all exclusions
    exclusions = origin_API.get_exclusions(origin_account_id)
    count=len(exclusions)
    print(f"Retrieved {count} exclusions")
    group_id_map, site_id_map = get_id_maps(origin_API, dest_API, origin_account_id, dest_account_id)
    print(f"Retrieved mapped Group and Site Ids")
    created_exclusions = []
    i=0

    for exclusion in exclusions:
        errors_list = []
        post_data={}
        try:
            ids = []
            ids = create_exclusion(dest_API, exclusion, dest_account_id, site_id_map, group_id_map)
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
