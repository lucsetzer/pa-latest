rom fastapi import FastAPI, Request, Form, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import sys
from pathlib import Path

print("🚀 dashboard/app.py starting...")
import traceback


# Add parent directory to path to import auth modules
sys.path.append(str(Path(__file__).parent.parent))

template_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=template_dir)

# Import from root directory
try:
    from bank_auth import verify_magic_link, create_magic_link
    from email_service import send_magic_link_email
except ImportError as e:
    print(f"Import error: {e}")
    # Mock functions for testing
    def verify_magic_link(token):
        return "test@example.com" if token else None
    def create_magic_link(email):
        return f"/auth?token=test_{email}"
    def send_magic_link_email(email):
        print(f"📨 MOCK: Magic link for {email}")
        return f"http://localhost:8000/auth?token=test_{email}"

app = FastAPI()

def get_user_balance(email: str):
    """Get user's token balance from bank database, create if doesn't exist"""
    db_path = Path(__file__).parent.parent / "bank.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Check if exists
    c.execute('SELECT tokens FROM accounts WHERE email = ?', (email,))
    result = c.fetchone()
    
    if result:
        balance = result[0]
    else:
        # Create new account with 0 tokens
        c.execute('INSERT INTO accounts (email, tokens) VALUES (?, ?)', (email, 0))
        conn.commit()
        balance = 0
        print(f"Created new account for {email}")
    
    conn.close()
    return balance

# Routes
@app.get("/")
async def public_root(request: Request):
    """Public frontpage - NO login required"""
    # Try multiple template locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "dashboard", "templates"),
        os.path.join(os.path.dirname(__file__), "templates"),
        "templates",
        "./templates"
    ]
    
    for template_dir in possible_paths:
        frontpage_path = os.path.join(template_dir, "frontpage.html")
        if os.path.exists(frontpage_path):
            print(f"✅ Found frontpage at: {frontpage_path}")
            templates = Jinja2Templates(directory=template_dir)
            return templates.TemplateResponse(
                "frontpage.html", 
                {"request": request, "app_name": "Prompts Alchemy"}
            )
    
    # Fallback if template not found
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prompts Alchemy</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    </head>
    <body>
        <main class="container">
            <h1>🔮 Prompts Alchemy</h1>
            <p>AI toolkit dashboard</p>
            <a href="/login" role="button">Login</a>
            <a href="/dashboard" role="button" secondary>Dashboard</a>
        </main>
    </body>
    </html>
    """)

@app.get("/which-app-dashboard")
async def which_app():
    return {"message": "This is COMBINED_APP", "path": "/dashboard"}




@app.post("/test-login")
async def test_login(request: Request, email: str = Form(...)):
    """Test login bypassing magic link for local development"""
    # Just set a test session
    test_token = "test_" + email
    response = RedirectResponse("/")
    response.set_cookie(key="session", value=test_token)
    return response


@app.get("/debug")
async def debug_all():
    """Show all routes and templates"""
    import os
    templates_dir = "templates"
    templates = os.listdir(templates_dir) if os.path.exists(templates_dir) else []
    
    return HTMLResponse(f"""
    <h1>Debug Info</h1>
    <h2>Routes:</h2>
    <ul>
        <li>GET / → dashboard (requires login)</li>
        <li>GET /login → login page</li>
        <li>POST /login → send magic link</li>
        <li>GET /auth → verify magic link</li>
        <li>GET /logout → clear session</li>
    </ul>
    <h2>Templates found:</h2>
    <ul>
        {"".join(f'<li>{t}</li>' for t in templates)}
    </ul>
    <h2><a href="/login">Go to login page</a></h2>
    """)
    
@app.get("/settings")
async def settings_page(request: Request, session: str = Cookie(default=None)):
    if not session:
        return RedirectResponse("/login")
    
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")
    
    balance = get_user_balance(email)
    
    # DEFINE current_plan here (mock for now)
    current_plan = "Free Tier"  # TODO: Get from database
    tokens_per_month = 15
    renewal_date = "2024-02-24"
    
    print(f"🔧 SETTINGS DEBUG: current_plan = {current_plan}")
    print(f"🔧 SETTINGS DEBUG: user_email = {email}")
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user_email": email,
        "balance": balance,
        "current_plan": current_plan,
        "tokens_per_month": tokens_per_month,
        "renewal_date": renewal_date
    })

@app.post("/generate-prompt")
async def generate_prompt(
    request: Request,
    goal: str = Form(...),
    audience: str = Form(...),
    platform: str = Form(...),
    style: str = Form(...),
    tone: str = Form(...),
    session: str = Cookie(default=None)
):
    """Generate a prompt using DeepSeek API with token checking"""
    
    # 1. AUTHENTICATION
    if not session:
        return RedirectResponse("/login?next=/prompt-wizard")
    
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")
    
    # 2. TOKEN CHECK (5 tokens for Prompt Wizard)
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Check balance
            balance_response = await client.get(
                f"http://localhost:8001/balance?email={email}",
                timeout=5.0
            )
            
            if balance_response.status_code == 200:
                balance = balance_response.json().get("balance", 0)
                if balance < 5:
                    return templates.TemplateResponse("insufficient_tokens.html", {
                        "request": request,
                        "balance": balance,
                        "required": 5,
                        "app_name": "Prompt Wizard"
                    })
            else:
                return layout("Bank Error", 
                    "<div class='card'><h2>Token system unavailable</h2></div>")
    except Exception as e:
        print(f"Token check error: {e}")
        return layout("System Error", 
            "<div class='card'><h2>Cannot connect to token system</h2></div>")
    
    # 3. DEEPSEEK API CALL
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return layout("Error", 
            "<div class='card'><h2>API not configured</h2><p>DeepSeek API key missing.</p></div>")
    
    prompt_text = f"""
    Create a {style} prompt for {audience} to achieve this goal: {goal}.
    Platform: {platform}
    Desired tone: {tone}
    
    Provide a complete, ready‑to‑use prompt.
    """
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a prompt engineering expert."},
                {"role": "user", "content": prompt_text}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated = result["choices"][0]["message"]["content"]
            
            # 4. DEDUCT TOKENS AFTER SUCCESS
            try:
                async with httpx.AsyncClient() as client:
                    spend_data = {
                        "email": email,
                        "app_id": "prompt_wizard",
                        "tokens": 5,
                        "description": f"Prompt: {goal[:50]}..."
                    }
                    spend_response = await client.post(
                        "http://localhost:8001/spend",
                        json=spend_data,
                        timeout=5.0
                    )
                    if spend_response.status_code != 200:
                        print(f"Token spend failed but prompt generated: {spend_response.text}")
            except Exception as e:
                print(f"Token spend error: {e}")
            
            # 5. RETURN RESULT
            return templates.TemplateResponse("prompt_result.html", {
                "request": request,
                "goal": goal,
                "audience": audience,
                "platform": platform,
                "style": style,
                "tone": tone,
                "generated_prompt": generated,
                "tokens_spent": 5
            })
            
        else:
            return layout("API Error", 
                f"<div class='card'><h2>API Error {response.status_code}</h2>"
                f"<p>{response.text}</p></div>")
                
    except Exception as e:
        return layout("Error", 
            f"<div class='card'><h2>Generation failed</h2><p>{str(e)}</p></div>")

@app.get("/prompt-wizard/intro")
async def prompt_wizard_intro(request: Request, session: str = Cookie(default=None)):
    """Prompt Wizard introduction page"""
    if not session:
        return RedirectResponse("/login?next=/prompt-wizard/intro")
    
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")
    
    return templates.TemplateResponse("prompt_wizard_intro.html", {
        "request": request,
        "user_email": email
    })

@app.get("/which-app-dashboard") 
async def which_app():
    return {"message": "This is DASHBOARD/APP", "path": "/dashboard"}

@app.get("/debug-file")
async def debug_file():
    import dashboard
    return {
        "dashboard_module": dashboard.__file__,
        "current_file": __file__
    }

print(f"🚨 LOADED: {__file__}")

print(f"🚨 dashboard/app.py LOADED. Routes being registered:")
for route in app.routes:
    print(f"  - {route.path}")

print(f"📁 dashboard/app.py template directory check")
print(f"📁 Current dir: {os.getcwd()}")
print(f"📁 Template search:")
for path in ["templates", "dashboard/templates", "./templates", "/opt/render/project/src/templates"]:
    exists = os.path.exists(os.path.join(path, "dashboard.html"))
    print(f"  - {path}/dashboard.html: {'✅' if exists else '❌'}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
