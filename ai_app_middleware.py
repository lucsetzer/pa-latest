# Add this to EACH of your 5 AI apps
import requests
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer('your-secret-key-here')

class TokenMiddleware:
    def __init__(self, app_id, dashboard_url):
        self.app_id = app_id
        self.dashboard_url = dashboard_url
    
    def check_and_spend(self, passport_token, operation, cost):
        """Verify passport and spend tokens before AI operation"""
        try:
            # Decrypt the passport
            passport = serializer.loads(passport_token, salt=f'passport-{self.app_id}')
            
            # Check if operation fits in budget
            if cost > passport["budget"]:
                return {"error": "Session budget exceeded"}, 403
            
            # Ask central bank to deduct tokens
            spend_request = {
                "email": passport["email"],
                "app_id": self.app_id,
                "tokens": cost,
                "description": operation
            }
            
            response = requests.post(
                f"{self.dashboard_url}/spend",
                json=spend_request
            )
            
            if response.status_code == 200:
                # Update passport budget
                passport["budget"] -= cost
                new_token = serializer.dumps(passport, salt=f'passport-{self.app_id}')
                return {"approved": True, "new_passport": new_token}
            else:
                return {"error": "Payment failed"}, 402
                
        except:
            return {"error": "Invalid passport"}, 401

# Usage in your existing AI app:
# middleware = TokenMiddleware(app_id="image_generator", dashboard_url="https://dashboard.yoursite.com")

# Before calling OpenAI:
# result = middleware.check_and_spend(passport_token, "generate_image", 50)
# if result["approved"]:
#     # Call AI API
#     # Update passport token in session
