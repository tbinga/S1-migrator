from configparser import ConfigParser
from s1_api import get_APIs
from migrators import get_migrators, migrate_structure

def get_name_to_id_map(node):
    returned_map = dict()
    for sub_node in node:
        returned_map[sub_node["name"]] = sub_node["id"]
    return returned_map

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

if __name__ == "__main__":
    #Parse config file
    parser = ConfigParser()
    parser.read("config.ini")
    origin_url = parser.get("settings", "origin_url") + "/web/api/v2.1/"
    dest_url = parser.get("settings", "dest_url") + "/web/api/v2.1/"
    origin_account_id = parser.get("settings", "origin_account_id")
    dest_account_id = parser.get("settings", "dest_account_id")
    origin_auth_header = {"Authorization": "ApiToken " + parser.get("settings", "origin_api_token")}
    dest_auth_header = {"Authorization": "ApiToken "  + parser.get("settings", "dest_api_token")}

    #Get APIs
    origin_APIs = get_APIs(origin_url, origin_auth_header, account_id=origin_account_id)
    dest_APIs = get_APIs(dest_url, dest_auth_header, account_id=dest_account_id)

    print("Copying sites and groups...")
    migrate_structure(origin_APIs["sites_and_groups"], dest_APIs["sites_and_groups"], origin_account_id, dest_account_id)

    #Retrieve ID maps
    group_id_map, site_id_map = get_id_maps(origin_APIs["sites_and_groups"], dest_APIs["sites_and_groups"], origin_account_id, dest_account_id)

    #Get migrators
    migrators = get_migrators(origin_APIs, dest_APIs, origin_account_id, dest_account_id, group_id_map, site_id_map)

    print("Copying exclusions...")
    migrators["exclusions"].migrate()

    print("Copying firewall rules...")
    migrators["firewall_rules"].migrate()
    
    """
    if origin_API.is_firewall_active(origin_account_id):
        print("Copying firewall rules...")
        migrate_firewall_rules(origin_API, dest_API, origin_account_id, dest_account_id)
    else:  
        print("Firewall is not active in the origin account. Skipping firewall rules migration.")
    
    if origin_API.is_network_quarantine_active(origin_account_id):
        print("Copying network quarantine rules...")
        migrate_network_quarantine(origin_API, dest_API, origin_account_id, dest_account_id)
    else:
        print("Network quarantine is not active in the origin account. Skipping network quarantine rules migration.")
    print("Copying device control rules...")
    migrate_device_control(origin_API, dest_API, origin_account_id, dest_account_id)
    """
