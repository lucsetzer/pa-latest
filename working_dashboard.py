from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import secrets

app = FastAPI()
sessions = {}

# SINGLE HTML with embedded form
HTML = '''
<!DOCTYPE html>
<html>
<body>
<script>
function login() {
    let email = document.getElementById("email").value;
    fetch("/login?email=" + email, {method: "POST"})
        .then(() => window.location.reload());
}
</script>
<h1>AI Wizards</h1>
<div id="content">
<!-- Dynamic content via JavaScript -->
</div>
<script>
fetch("/api/status").then(r => r.json()).then(data => {
    if (data.logged_in) {
        document.getElementById("content").innerHTML = `
            <p>Email: ${data.email}</p>
            <h2>Tokens: ${data.balance}</h2>
            <button onclick="fetch('/logout').then(() => location.reload())">Logout</button>
        `;
    } else {
        document.getElementById("content").innerHTML = `
            <input id="email" placeholder="you@example.com">
            <button onclick="login()">Login</button>
        `;
    }
});
</script>
</body>
</html>
'''

@app.get("/")
async def home():
    return HTMLResponse(HTML)

@app.get("/api/status")
async def status(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return {"logged_in": False}
    
    email = sessions[session_id]
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute('SELECT tokens FROM accounts WHERE email = ?', (email,))
    result = c.fetchone()
    balance = result[0] if result else 0
    conn.close()
    
    return {"logged_in": True, "email": email, "balance": balance}

@app.post("/login")
async def login(email: str):
    session_id = secrets.token_hex(16)
    sessions[session_id] = email
    response = RedirectResponse("/")
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie(key="session_id")
    return response

print(f"🚨 LOADED: {__file__}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
