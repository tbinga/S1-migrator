from configparser import ConfigParser
from exclusions_migrator import migrate_exclusions
from structure_migrator import migrate_structure
from s1_api import S1Api

if __name__ == "__main__":
    parser = ConfigParser()
    parser.read("config.ini")
    origin_url = parser.get("settings", "origin_url") + "/web/api/v2.1/"
    dest_url = parser.get("settings", "dest_url") + "/web/api/v2.1/"
    origin_account_id = parser.get("settings", "origin_account_id")
    dest_account_id = parser.get("settings", "dest_account_id")
    origin_auth_header = {"Authorization": "ApiToken " + parser.get("settings", "origin_api_token")}
    dest_auth_header = {"Authorization": "ApiToken "  + parser.get("settings", "dest_api_token")}
    origin_API = S1Api(origin_url, origin_auth_header)
    dest_API = S1Api(dest_url, dest_auth_header)
    print("Copying sites and groups...")
    migrate_structure(origin_API, dest_API, origin_account_id, dest_account_id)
    print("Copying exclusions...")
    migrate_exclusions(origin_API, dest_API, origin_account_id, dest_account_id)