# shop/api_service.py
import requests
from django.conf import settings

API_BASE_URL = "http://127.0.0.1:5000/api"

class ECommerceAPI:
    
    @staticmethod
    def get_all_items(category=None):
        """Fetch all products from API"""
        try:
            params = {}
            if category:
                params['category'] = category
            response = requests.get(f"{API_BASE_URL}/items", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return []
    
    @staticmethod
    def get_item_by_id(item_id):
        """Fetch specific product from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/items/{item_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    @staticmethod
    def create_order(customer_name, customer_email, items):
        """Create new order via API
        
        items = [
            {"item_id": 1, "quantity": 2},
            {"item_id": 3, "quantity": 1}
        ]
        """
        try:
            order_data = {
                "customer_name": customer_name,
                "customer_email": customer_email,
                "items": items
            }
            response = requests.post(
                f"{API_BASE_URL}/orders",
                json=order_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    @staticmethod
    def get_order_by_id(order_id):
        """Fetch order details from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/orders/{order_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    @staticmethod
    def update_order(order_id, quantity=None, status=None):
        """Update order via API"""
        try:
            update_data = {}
            if quantity:
                update_data["quantity"] = quantity
            if status:
                update_data["status"] = status
            
            response = requests.put(
                f"{API_BASE_URL}/orders/{order_id}",
                json=update_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    @staticmethod
    def delete_order(order_id):
        """Delete order via API"""
        try:
            response = requests.delete(f"{API_BASE_URL}/orders/{order_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    @staticmethod
    def get_all_transactions(status=None):
        """Fetch all sales transactions from API"""
        try:
            params = {}
            if status:
                params['status'] = status
            response = requests.get(f"{API_BASE_URL}/transactions", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return []