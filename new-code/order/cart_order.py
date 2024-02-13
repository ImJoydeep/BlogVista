from django.db import transaction
from order.models import OrderMaster
from order.utility import calling_magento, magento_orders
from product.models.models_item import Item


def create_cart():
    cart_url = "rest/default/V1/carts/"
    try:
        response = calling_magento("post", cart_url)
        if response.status_code == 200:
            cart_id = int(response.json())
            return cart_id
    except Exception:
        return None

def check_mail_id_magento(email):
    customer_id = None
    email_check_url = f"rest/default/V1/customers/search?searchCriteria[filterGroups][0][filters][0][field]=email&searchCriteria[filterGroups][0][filters][0][value]={email}"
    resposne = calling_magento("get", email_check_url)
    resposne = resposne.json()
    if len(resposne.get("items")[0]) > 0:
        customer_id = resposne.get("items")[0]["id"]
    return customer_id


def add_billing_cart(data, customer_id, cart_id):
    billing_address = {
        "address": {
            "region": data.get("OD_BA_RGN"),
            "region_id": 64,
            "region_code": "ID",
            "country_id": data.get("OD_BA_CTR_CODE"),
            "street": [
                data.get("OD_BA_ST")
            ],
            "telephone": data.get("CUST_PH"),
            "postcode": data.get("OD_BA_PIN"),
            "city": data.get("OD_BA_CT"),
            "firstname": data.get("OD_BA_FN"),
            "lastname": data.get("OD_BA_LN"),
            "customer_id": customer_id,
            "email": data.get("OD_BA_EMAIL")
        }
    }
    billing_address_url = f"rest/default/V1/carts/{cart_id}/billing-address"
    try:
        response = calling_magento('post', billing_address_url, payload=billing_address)
        return response
    except Exception:
        return None

def add_shipping_cart(data, customer_id, cart_id):
    shipping_address = {
        "addressInformation": {
            "shipping_address": {
                "region": data.get("OD_SA_RGN"),
                "region_id": 64,
                "region_code": "ID",
                "country_id": data.get("OD_SA_CTR_CODE"),
                "street": [data.get("OD_SA_ST")],
                "telephone": data.get("CUST_PH"),
                "postcode": data.get("OD_SA_PIN"),
                "city": data.get("OD_SA_CT"),
                "firstname": data.get("OD_SA_FN"),
                "lastname": data.get("OD_SA_LN"),
                "customer_id": customer_id,
                "email": data.get("OD_SA_EMAIL")
                },
                "shipping_method_code": "flatrate",
                "shipping_carrier_code": "flatrate"
            }
        }
    shipping_url = f"rest/default/V1/carts/{cart_id}/shipping-information"
    try:
        response = calling_magento('post', shipping_url, payload=shipping_address)
        return response
    except Exception:
        return None

def add_order(data, cart_id):
    status = False
    order_data = {
        "paymentMethod": {
            "method": data.get("PT_MD_NM"),
            "additional_data": [],
            "extension_attributes": {
                "agreement_ids": []
            }
        }
    }
    order_url = f"rest/default/V1/carts/{cart_id}/order"
    response = calling_magento('put', order_url, payload=order_data)
    if response.status_code == 200:
        status = True
    return response, status


def add_item_cart_detail(data):
    cart_id = create_cart()
    get_cart_url = f"rest/V1/carts/{cart_id}"
    try:
        calling_magento("get", get_cart_url)
        cart_add_item_url = f"/rest/default/V1/carts/{cart_id}/items"
        for item in data.get("items"):
            product = Item.objects.filter(
                AS_ITM_SKU=item.get("AS_ITM_SKU")).first()
            item_payload = {
                "cartItem":
                {
                    "sku": product.AS_ITM_SKU,
                    "qty": int(item.get("OD_ITM_QTY")),
                    "name": product.NM_ITM,
                    "price": item.get("OD_ITM_OR_PR"),
                    "product_type": product.AS_ITM_TYPE,
                    "quote_id": str(cart_id)
                }
            }
            calling_magento("post", cart_add_item_url, payload=item_payload)

        #Customer info
        customer_mapping_url = f"rest/default/V1/carts/{cart_id}"
        customer_id = check_mail_id_magento(data.get("CUST_EMAIL"))
        customer_mapping_payload = {
            "customerId": customer_id,
            "storeId": data.get("OD_STR_ID"),
            "locationId": 3
        }
        customer_mapping_resposne = calling_magento("put", customer_mapping_url, payload=customer_mapping_payload)
        is_customer = customer_mapping_resposne.text
        if is_customer:
            add_billing_cart(data, customer_id, cart_id)
            add_shipping_cart(data, customer_id, cart_id)
            order_info = add_order(data, cart_id)
            if order_info[1]:
                with transaction.atomic():
                    magento_orders()
            return int(order_info[0]), order_info[1]
        
    except Exception:
        return None, None   
