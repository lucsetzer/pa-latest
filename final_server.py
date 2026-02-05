#!/usr/bin/env python3
"""
ULTRA-SIMPLE Dashboard - No dependencies, just Python
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import secrets
import urllib.parse
import json

sessions = {}

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Check session
            session_id = self.get_cookie('session_id')
            if session_id in sessions:
                email = sessions[session_id]
                balance = self.get_balance(email)
                html = f"""
                <html><body>
                <h1>AI Wizards Dashboard</h1>
                <p>Email: {email}</p>
                <h2>Tokens: {balance}</h2>
                <a href="/logout">Logout</a>
                </body></html>
                """
            else:
                html = """
                <html><body>
                <h1>AI Wizards Login</h1>
                <form action="/login" method="post">
                <input type="email" name="email" placeholder="you@example.com">
                <button>Login</button>
                </form>
                </body></html>
                """
            
            self.wfile.write(html.encode())
            
        elif self.path == '/logout':
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', 'session_id=; Max-Age=0')
            self.end_headers()
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            params = urllib.parse.parse_qs(post_data)
            email = params.get('email', [''])[0]
            
            if email:
                session_id = secrets.token_hex(16)
                sessions[session_id] = email
                
                self.send_response(302)
                self.send_header('Location', '/')
                self.send_header('Set-Cookie', f'session_id={session_id}; Path=/')
                self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
    
    def get_cookie(self, name):
        cookie_header = self.headers.get('Cookie', '')
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if cookie.startswith(f'{name}='):
                return cookie.split('=', 1)[1]
        return None
    
    def get_balance(self, email):
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        c.execute('SELECT tokens FROM accounts WHERE email = ?', (email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def log_message(self, format, *args):
        pass  # Silence logs

def run():
    print("🚀 Dashboard running at http://localhost:8080")
    print("📊 Bank API at http://localhost:8000")
    print("💡 Login with: luc@test.com (has 1450 tokens)")
    server = HTTPServer(('localhost', 8080), DashboardHandler)
    server.serve_forever()

if __name__ == '__main__':
    run()
