# thumbnail_proxy.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os

app = FastAPI()
CENTRAL_BANK = "http://localhost:8000"  # Your token bank
REAL_APP = "http://localhost:5001"      # Your actual thumbnail app

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(request: Request, path: str):
    # 1. Get user's token from cookie/session
    user_token = request.cookies.get("dashboard_token")
    if not user_token:
        return RedirectResponse("https://dashboard.yourplatform.com/login")
    
    # 2. Ask central bank: "Can this user spend 4 tokens?"
    try:
        check = httpx.post(f"{CENTRAL_BANK}/can_spend", json={
            "token": user_token,
            "app": "thumbnail_wizard",
            "cost": 4
        })
        
        if check.status_code != 200:
            # Not enough tokens
            return RedirectResponse("https://dashboard.yourplatform.com/buy-tokens")
    
    except:
        # Bank is down
        return {"error": "Bank unavailable"}, 503
    
    # 3. Forward to real app
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=f"{REAL_APP}/{path}",
            headers=dict(request.headers),
            content=await request.body()
        )
    
    return response.content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)  # Proxy on port 8002
