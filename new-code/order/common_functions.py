import requests
import json
from taxonomy.taxonomy_magento_integration import magento_login


application_json_key = "application/json"


def check_email(email):
    magento_token, magento_url = magento_login()
    magento_contact_check_url = magento_url + \
        f"/rest/default/V1/customers/search?searchCriteria[filterGroups][0][filters][0][field]=email&searchCriteria[filterGroups][0][filters][0][value]={email}"
    headers = {"content-type": application_json_key}
    magento_customer_info = requests.get(
        url=magento_contact_check_url, headers=headers, auth=magento_token)
    magento_customer_info = json.loads(magento_customer_info.text)
    if len(magento_customer_info.get("items")) > 0:
        return True, magento_customer_info.get("items")
    else:
        return False, None
