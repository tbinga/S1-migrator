from abc import abstractmethod, ABC
convert_ids = lambda ids, map: [str(map[id]) for id in ids]

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
        if dest_site_id == None:
            continue
        groups = origin_API.get_groups(origin_account_id, site.get("id"))
        for group in groups:
            if group.get("name") == "Default Group":
                continue
            if group.get("inherits") == False:
                group["policy"] = origin_API.get_group_policy(group.get("id"))
            dest_group = adapt_group(group, dest_account_id, dest_site_id)
            dest_group_id = dest_API.create_group(dest_group)

class Migrator(ABC):
    def __init__(self, origin_API, dest_API, origin_account_id, dest_account_id, group_id_map, site_id_map):
        self.origin_API = origin_API
        self.dest_API = dest_API
        self.origin_account_id = origin_account_id
        self.dest_account_id = dest_account_id
        self.group_id_map, self.site_id_map = group_id_map, site_id_map
        self.object_name = None

    def _parse_scope(self, data):
        return data.get("scope").get("siteIds"), data.get("scope").get("groupIds")
    
    """Method used to adapt the data to be migrated. (e.g. remove fields that are not needed in the destination console))"""
    @abstractmethod
    def _adapt(self, data):
        pass

    def _get_filter(self, data):
        site_ids, group_ids = self._parse_scope(data)
        if group_ids: #Group exclusion
            filter = {
        "groupIds": convert_ids(group_ids, self.group_id_map),
        "tenant": "true"
            }
        elif site_ids: #Site exclusion
            filter = {
        "siteIds": convert_ids(site_ids, self.site_id_map),
        "tenant": "true"
            }
        else : #Account exclusion
            filter = {
        "accountIds": [str(self.dest_account_id)],
        "tenant": "true"
            }
        return filter

    def create(self, data):
        new_data = self._adapt(data)
        filter = self._get_filter(data)
        post_data = {"filter": filter, "data": new_data}
        return self.dest_API.create(post_data)

    def migrate(self):
        created_ids = []
        objects_to_migrate = self.origin_API.get()
        for object in objects_to_migrate:
            new_id = self.create(object)
            created_ids.append(new_id) if new_id else None
        return created_ids
            
class ExclusionsMigrator(Migrator):
    def __init__(self, origin_API, dest_API, origin_account_id, dest_account_id, group_id_map, site_id_map):
        super().__init__(origin_API, dest_API, origin_account_id, dest_account_id, group_id_map, site_id_map)
        self.object_name = "exclusion"

    def _adapt(self, data):
        exclusion_type = data.get("type")
        actions = [] if data.get("actions") == None else data.get("actions")
        new_data ={
            "type": exclusion_type,
            "value": data.get("value"),
            "description": data.get("description"),
            "source": data.get("source"),
            "actions": actions,
            "osType": data.get("osType"),
            }
        for field in ["pathExclusionType", "mode"]:
            if data.get(field):
                new_data[field] = data.get(field)
        return new_data
        
class FirewallRulesMigrator(Migrator):
    def __init__(self, origin_API, dest_API, origin_account_id, dest_account_id, group_id_map, site_id_map):
        super().__init__(origin_API, dest_API, origin_account_id, dest_account_id, group_id_map, site_id_map)
        self.object_name = "firewall rule"
    
    def _adapt(self, data):
        return super()._adapt(data)

def get_migrators(origin_APIs, dest_APIs, origin_account_id, dest_account_id, group_id_map, site_id_map):
    return {
    "exclusions": ExclusionsMigrator(origin_APIs["exclusions"], dest_APIs["exclusions"], origin_account_id, dest_account_id, group_id_map, site_id_map),
    "firewall_rules" : FirewallRulesMigrator(origin_APIs["firewall_rules"], dest_APIs["firewall_rules"], origin_account_id, dest_account_id, group_id_map, site_id_map)
    }