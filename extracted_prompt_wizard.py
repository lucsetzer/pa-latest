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
