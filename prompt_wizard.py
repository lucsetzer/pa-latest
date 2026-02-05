print("🟢 1. Script starting...")


from fastapi import Request, Query, APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests
import json
#import results

router = APIRouter()


# ========== ICON MAPPING ==========
ICON_MAP = {
    # Goals
    "explain": "fa-solid fa-comment-dots",
    "create": "fa-solid fa-lightbulb",
    "analyze": "fa-solid fa-chart-bar",
    "solve": "fa-solid fa-puzzle-piece",
    "brainstorm": "fa-solid fa-brain",
    "edit": "fa-solid fa-pen-to-square",
    
    # Audiences
    "general": "fa-solid fa-users",
    "experts": "fa-solid fa-user-tie",
    "students": "fa-solid fa-graduation-cap",
    "business": "fa-solid fa-briefcase",
    "technical": "fa-solid fa-code",
    "beginners": "fa-solid fa-person-circle-question",
    
    # Platforms
    "chatgpt": "fa-solid fa-comment",
    "claude": "fa-solid fa-robot",
    "gemini": "fa-solid fa-search",
    "deepseek": "fa-solid fa-rocket",
    "perplexity": "fa-solid fa-book",
    "copilot": "fa-solid fa-terminal",
    
    # Styles
    "direct": "fa-solid fa-bullseye",
    "structured": "fa-solid fa-layer-group",
    "creative": "fa-solid fa-palette",
    "technical": "fa-solid fa-microchip",
    "conversational": "fa-solid fa-comments",
    "step-by-step": "fa-solid fa-shoe-prints",
    
    # Tones
    "professional": "fa-solid fa-suitcase",
    "friendly": "fa-solid fa-face-smile",
    "authoritative": "fa-solid fa-graduation-cap",
    "enthusiastic": "fa-solid fa-fire",
    "neutral": "fa-solid fa-balance-scale",
    "humorous": "fa-solid fa-face-laugh-beam",
}

# ========== CORE LAYOUT FUNCTION ==========
def layout(title: str, content: str, step: int = 1) -> HTMLResponse:
    """Base layout with aqua blue theme and progress bar"""
    
    # Calculate progress percentage
    progress_percent = (step / 6) * 100 if step <= 6 else 100
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00f5d4;      /* Aqua blue */
            --primary-hover: #00b4a0; /* Dark turquoise */
            --primary-focus: rgba(0, 245, 212, 0.2);
        }}
        
        /* Apply theme to Pico.css */
        a, [role="button"] {{
            --pico-primary: var(--primary);
            --pico-primary-hover: var(--primary-hover);
            --pico-primary-focus: var(--primary-focus);
        }}
        
        .step-card {{
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
            min-height: 180px;
            justify-content: center;
        }}
        
        .step-card:hover {{
            border-color: var(--primary);
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0, 245, 212, 0.15);
            background: rgba(0, 245, 212, 0.03);
        }}
        
        .step-icon {{
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        
        /* Progress bar */
        .progress-container {{
            margin: 2rem 0;
        }}
        
        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary), #00d9ff);
            width: {progress_percent}%;
            transition: width 0.5s ease;
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #666;
        }}
        
        .progress-step {{
            text-align: center;
            flex: 1;
        }}
        
        .progress-step.active {{
            color: var(--primary);
            font-weight: bold;
        }}
        
        /* Loading animation for AI */
        .loading-ai {{
            text-align: center;
            padding: 3rem;
        }}
        
        .loading-dots {{
            display: inline-block;
        }}
        
        .loading-dots span {{
            animation: pulse 1.5s infinite;
            opacity: 0.3;
            display: inline-block;
            font-size: 2rem;
            margin: 0 0.25rem;
        }}
        
        .loading-dots span:nth-child(2) {{ animation-delay: 0.3s; }}
        .loading-dots span:nth-child(3) {{ animation-delay: 0.6s; }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.3; transform: scale(0.9); }}
            50% {{ opacity: 1; transform: scale(1.1); }}
        }}
        


        # Add these styles to the layout function's CSS:

/* Document-style prompt output */
.document-output {{
    background: white;
    color: #374151;
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    font-size: 0.95rem;
    white-space: pre-wrap;
    position: relative;
    margin: 2rem 0;
    line-height: 1.5;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    max-width: 100%;
    overflow-x: auto;
}}

/* Remove bold from everything except headers */
.document-output *:not(h2):not(h3):not(h4) {{
    font-weight: normal !important;
}}

.document-output h2 {{
  color: #111827;
    margin-top: 1.5em;
    margin-bottom: 0.75em;
    border-bottom: 2px solid var(--primary);
    padding-bottom: 0.5rem;
    font-weight: 600;
    font-size: 1.25rem;
}} 
.document-output h3 {{
  color: #1f2937;
    margin-top: 1.25em;
    margin-bottom: 0.5em;
    font-weight: 600;
    font-size: 1.1rem;
}} 
.document-output h4 {{
    color: #111827;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}}

.document-output h2 {{
    border-bottom: 2px solid var(--primary);
    padding-bottom: 0.5rem;
}}

.document-output ul, 
.document-output ol {{
    padding-left: 1.5rem;
    margin: 1rem 0;
}}

.document-output li {{
    margin-bottom: 0.5rem;
}}

.document-output code {{
    background: #f3f4f6;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}}

.document-output pre {{
    background: #f8fafc;
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
    overflow-x: auto;
    margin: 1rem 0;
}}

/* Formatting for the AI's markdown-like output */
.document-output .prompt-section {{
    margin-bottom: 2rem;
}}

.document-output .prompt-section:last-child {{
    margin-bottom: 0;
}}



        /* Prompt output styling - FIXED for better readability */
        # In the layout function, find the .prompt-output and .copy-button CSS and replace with:

.prompt-output {{
    background: #0f172a;
    color: #e2e8f0;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #334155;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    position: relative;
    margin: 1.5rem 0;
    line-height: 1.6;
    min-height: 200px;
}}
    </style>
</head>
<body>
        <nav class="container">
        <ul>
            <li><strong><a href="/dashboard" style="text-decoration:none; color: var(--primary);">
                <i class="fas fa-flask"></i> Prompts Alchemy
            </a></strong></li>
        </ul>
        <ul>
            <li><a href="/dashboard"><i class="fas fa-home"></i> Dashboard</a></li>
            <li><a href="/prompt-wizard/step/1"><i class="fas fa-magic"></i> Prompt Wizard</a></li>
            <li><a href="/script-wizard"><i class="fas fa-scroll"></i> Script Wizard</a></li>
        </ul>
    </nav>
    
    <main class="container">
        {content}
    </main>
    
    <script>
        // Copy to clipboard function
        function copyPrompt() {{
            const promptElement = document.querySelector('.prompt-output');
            const text = promptElement.textContent;
            
            navigator.clipboard.writeText(text).then(() => {{
                const button = document.querySelector('.copy-button');
                if (button) {{
                    const originalHTML = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    button.style.background = '#10b981';
                    
                    setTimeout(() => {{
                        button.innerHTML = originalHTML;
                        button.style.background = '';
                    }}, 2000);
                }}
            }}).catch(err => {{
                console.error('Copy failed:', err);
                // Fallback: select text
                const range = document.createRange();
                range.selectNode(promptElement);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand('copy');
                alert('Text selected - press Ctrl+C to copy');
            }});
        }}
        
        // Auto-scroll to output
        function scrollToOutput() {{
            const output = document.querySelector('.prompt-output');
            if (output) {{
                output.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
        }}
    </script>
</body>
</html>'''
    return HTMLResponse(content=html)

# ========== DEEPSEEK API FUNCTION ==========
def call_deepseek_api(goal: str, audience: str, tone: str, platform: str, user_prompt: str) -> str:
    """Call DeepSeek API to generate optimized prompt"""
    
    system_prompt = """You are a Prompt Engineering Expert. Create optimized, structured prompts.

CRITICAL RULES:
1. DO NOT answer the user's question
2. DO NOT provide solutions or content
3. ONLY create the prompt structure
4. Make it DETAILED and READY-TO-USE

EXAMPLE OUTPUT:
## Role: Quantum Physics Educator
## Task: Explain quantum computing to beginners
## Requirements: Use simple analogies, avoid math, focus on core concepts
## Format: Clear headings, bullet points, step-by-step"""

    user_message = f"""Create a STRUCTURED prompt for this request:

ORIGINAL REQUEST: "{user_prompt}"
CONTEXT:
- Goal: {goal}
- Target Audience: {audience}
- Desired Tone: {tone}
- Target AI Platform: {platform}

Make it DETAILED and READY-TO-USE. The user will copy-paste this into {platform}."""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            prompt = result["choices"][0]["message"]["content"].strip()
            
            # Ensure proper formatting
            if not prompt.startswith("##"):
                prompt = f"## AI-Optimized Prompt for {platform}\n\n{prompt}"
                
            return prompt
        else:
            return f"## Error: API returned status {response.status_code}\n\n{response.text}"
            
    except Exception as e:
        return f"## Error: {str(e)}\n\n## Fallback Prompt Structure:\n\nRole: AI Assistant\nTask: {user_prompt}\nAudience: {audience}\nTone: {tone}\nFormat: Structured response"


print("🟢 2. Before route definitions...")


# ========== HOME PAGE ==========
@router.get("/")
async def home():
    content = '''
    <article style="text-align: center; padding: 3rem 0;">
        <h1>🧙 Prompt Wizard</h1>
        <p class="lead" style="font-size: 1.25rem; color: #666; margin: 1rem 0 2rem 0;">
            Transform simple ideas into powerful AI prompts
        </p>
        
        <div style="max-width: 600px; margin: 0 auto 3rem auto; text-align: left;">
            <div class="card" style="margin-bottom: 1rem;">
                <h4><i class="fas fa-brain" style="color: var(--primary);"></i> auDHD Friendly</h4>
                <p>Clickable cards, clear steps, no overwhelm</p>
            </div>
            
            <div class="card" style="margin-bottom: 1rem;">
                <h4><i class="fas fa-magic" style="color: var(--primary);"></i> 6-Step Process</h4>
                <p>Simple choices → Professional prompt</p>
            </div>
            
            <div class="card">
                <h4><i class="fas fa-robot" style="color: var(--primary);"></i> DeepSeek AI Powered</h4>
                <p>Advanced prompt optimization</p>
            </div>
        </div>
        
        <a href="/prompt-wizard/step/1" role="button" class="primary" style="padding: 1rem 2rem; font-size: 1.1rem;">
            <i class="fas fa-play-circle"></i> Start Wizard
        </a>
        
        <div style="margin-top: 3rem; color: #888; font-size: 0.9rem;">
            <p>No login required • All processing happens in your browser • Free to use</p>
        </div>
    </article>
    '''
    return layout("Home - Prompt Wizard", content, step=0)

# ========== STEP 1: GOAL SELECTION ==========
@router.get("/prompt-wizard/step/1")
async def step1():
    goals = [
        ("explain", "Explain", "Break down complex topics"),
        ("create", "Create", "Generate content or ideas"),
        ("analyze", "Analyze", "Review data or text"),
        ("solve", "Solve", "Find solutions to problems"),
        ("brainstorm", "Brainstorm", "Generate possibilities"),
        ("edit", "Edit/Improve", "Refine existing content"),
    ]
    
    goal_cards = ""
    for value, label, description in goals:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        goal_cards += f'''
        <a href="/prompt-wizard/step/2?goal={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 1: What's your goal?</h1>
                <p>What do you want the AI to help you with?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step active">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {goal_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/" class="secondary">
                <i class="fas fa-home"></i> Back to Home
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 1: Goal Selection", content, step=1)
# ========== STEP 2: AUDIENCE SELECTION ==========
@router.get("/prompt-wizard/step/2")
async def step2(goal: str = Query("explain")):
    audiences = [
        ("general", "General Public", "Anyone without specific expertise"),
        ("experts", "Experts", "People with deep knowledge"),
        ("students", "Students", "Learners at various levels"),
        ("business", "Business", "Professionals, clients, stakeholders"),
        ("technical", "Technical", "Developers, engineers, scientists"),
        ("beginners", "Beginners", "New to the topic, need basics"),
    ]
    
    audience_cards = ""
    for value, label, description in audiences:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        audience_cards += f'''
        <a href="/prompt-wizard/step/3?goal={goal}&audience={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 2: Who is your audience?</h1>
                <p>Who will read or use this output?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step active">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected Goal:</strong> {goal.capitalize()}</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {audience_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/1" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 1
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 2: Audience Selection", content, step=2)
# ========== STEP 3: PLATFORM SELECTION ==========
@router.get("/prompt-wizard/step/3")
async def step3(goal: str = Query("explain"), audience: str = Query("general")):
    platforms = [
        ("chatgpt", "ChatGPT", "OpenAI's conversational AI"),
        ("claude", "Claude", "Anthropic's thoughtful assistant"),
        ("gemini", "Gemini", "Google's multimodal AI"),
        ("deepseek", "DeepSeek", "DeepSeek AI models"),
        ("perplexity", "Perplexity", "Research-focused with citations"),
        ("copilot", "GitHub Copilot", "Code completion and generation"),
    ]
    
    platform_cards = ""
    for value, label, description in platforms:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        platform_cards += f'''
        <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&platform={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 3: Which AI platform?</h1>
                <p>Where will you use this prompt?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step active">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} audience</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {platform_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/2?goal={goal}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 2
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 3: Platform Selection", content, step=3)
# ========== STEP 4: STYLE SELECTION ==========
@router.get("/prompt-wizard/step/4")
async def step4(goal: str = Query("explain"), audience: str = Query("general"), platform: str = Query("chatgpt")):
    styles = [
        ("direct", "Direct", "Straight to the point"),
        ("structured", "Structured", "Organized with headings"),
        ("creative", "Creative", "Imaginative, free-flowing"),
        ("technical", "Technical", "Detailed with specifications"),
        ("conversational", "Conversational", "Natural, chat-like"),
        ("step-by-step", "Step-by-Step", "Guided instructions"),
    ]
    
    style_cards = ""
    for value, label, description in styles:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        style_cards += f'''
        <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&platform={platform}&style={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 4: What style do you prefer?</h1>
                <p>How should the AI structure its response?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step active">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} on {platform.capitalize()}</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {style_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/3?goal={goal}&audience={audience}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 3
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 4: Style Selection", content, step=4)
# ========== STEP 5: TONE SELECTION ==========
@router.get("/prompt-wizard/step/5")
async def step5(goal: str = Query("explain"), audience: str = Query("general"), 
                platform: str = Query("chatgpt"), style: str = Query("direct")):
    tones = [
        ("professional", "Professional", "Formal, business-appropriate"),
        ("friendly", "Friendly", "Warm, approachable, casual"),
        ("authoritative", "Authoritative", "Confident, expert-like"),
        ("enthusiastic", "Enthusiastic", "Energetic, passionate"),
        ("neutral", "Neutral", "Objective, unbiased"),
        ("humorous", "Humorous", "Funny, lighthearted"),
    ]
    
    tone_cards = ""
    for value, label, description in tones:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        tone_cards += f'''
        <a href="/prompt-wizard/step/6?goal={goal}&audience={audience}&platform={platform}&style={style}&tone={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 5: What tone should it use?</h1>
                <p>The overall mood or attitude of the response</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step active">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} on {platform.capitalize()} in {style} style</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {tone_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&platform={platform}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 4
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 5: Tone Selection", content, step=5)
# ========== STEP 6: PROMPT INPUT ==========
@router.get("/prompt-wizard/step/6")
async def step6(goal: str = Query("explain"), audience: str = Query("general"), 
                platform: str = Query("chatgpt"), style: str = Query("direct"), 
                tone: str = Query("professional")):
    
    # Create a summary of selections
    selections = f'''
    <div class="card secondary" style="margin: 1rem 0 2rem 0;">
        <div class="grid" style="grid-template-columns: repeat(5, 1fr); gap: 0.5rem; text-align: center;">
            <div>
                <small>Goal</small><br>
                <strong>{goal.capitalize()}</strong>
            </div>
            <div>
                <small>Audience</small><br>
                <strong>{audience.capitalize()}</strong>
            </div>
            <div>
                <small>Platform</small><br>
                <strong>{platform.capitalize()}</strong>
            </div>
            <div>
                <small>Style</small><br>
                <strong>{style.replace('-', ' ').title()}</strong>
            </div>
            <div>
                <small>Tone</small><br>
                <strong>{tone.capitalize()}</strong>
            </div>
        </div>
    </div>
    '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 6: Enter Your Prompt</h1>
                <p>Type your original prompt, and AI will optimize it</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step active">6. Prompt</div>
                </div>
            </div>
            
            {selections}
        </header>
        
        <form id="promptForm" action="/prompt-wizard/generate" method="get" 
              onsubmit="showLoading(); return true;">
            <!-- Hidden fields to pass selections -->
            <input type="hidden" name="goal" value="{goal}">
            <input type="hidden" name="audience" value="{audience}">
            <input type="hidden" name="platform" value="{platform}">
            <input type="hidden" name="style" value="{style}">
            <input type="hidden" name="tone" value="{tone}">
            
            <div class="grid">
                <div>
                    <label for="user_prompt">
                        <h3>Your Original Prompt:</h3>
                        <p>Type what you'd normally ask the AI</p>
                    </label>
                    <textarea 
                        id="user_prompt" 
                        name="prompt" 
                        rows="8" 
                        placeholder="Example: 'Explain quantum computing like I'm 5' or 'Write a blog post about climate change'"
                        required
                        style="font-size: 1rem; padding: 1rem;"
                    ></textarea>
                </div>
                
                <div>
                    <h3>Tips for Great Prompts:</h3>
                    <div class="card" style="height: 100%;">
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            <li>Be specific about what you want</li>
                            <li>Include context when relevant</li>
                            <li>Mention length or format if needed</li>
                            <li>Add examples if helpful</li>
                            <li>Don't worry about perfection - AI will optimize it!</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button type="submit" class="primary" style="padding: 1rem 2rem; font-size: 1.1rem;">
                    <i class="fas fa-magic"></i> Generate Optimized Prompt
                </button>
                
                <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&platform={platform}&style={style}" 
                   class="secondary" style="margin-left: 1rem;">
                    <i class="fas fa-arrow-left"></i> Back
                </a>
            </div>
        </form>
        
        <!-- Loading animation (hidden by default) -->
        <div id="loading" style="display: none; text-align: center; padding: 3rem;">
            <div class="loading-ai">
                <div class="loading-dots">
                    <span>●</span>
                    <span>●</span>
                    <span>●</span>
                </div>
                <h3 style="margin-top: 1rem;">AI is working its magic...</h3>
                <p>This usually takes 10-30 seconds</p>
                <div class="progress-bar" style="max-width: 400px; margin: 2rem auto;">
                    <div class="progress-fill" style="width: 100%; animation: pulse 2s infinite;"></div>
                </div>
                <p><small>Do not refresh the page</small></p>
            </div>
        </div>
    </article>
    
    <script>
        function showLoading() {{
            // Show loading animation
            document.getElementById('loading').style.display = 'block';
            
            // Hide form
            document.getElementById('promptForm').style.display = 'none';
            
            // Scroll to loading
            document.getElementById('loading').scrollIntoView({{ behavior: 'smooth' }});
        }}
    </script>
    '''
    
    return layout("Step 6: Enter Your Prompt", content, step=6)
# ========== GENERATE FINAL PROMPT ==========
@router.get("/prompt-wizard/generate")
async def generate_prompt(
    goal: str = Query("explain"),
    audience: str = Query("general"),
    platform: str = Query("chatgpt"),
    style: str = Query("direct"),
    tone: str = Query("professional"),
    prompt: str = Query(""),
):
    """GET route - works with URL parameters"""
    
    # Token check happens automatically before this point
    # If tokens insufficient, HTTPException is raised
    
    # Call DeepSeek API with your parameters
    optimized_prompt = call_deepseek_api(goal, audience, tone, platform, prompt)
    
    # Your entire HTML template logic stays EXACTLY the same
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1><i class="fas fa-check-circle" style="color: var(--primary);"></i> Prompt Ready!</h1>
                <p>Your AI-optimized prompt for {platform.capitalize()}</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step active">Complete!</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 800px; text-align: left;">
                <div class="grid" style="grid-template-columns: repeat(5, 1fr); gap: 0.5rem; text-align: center;">
                    <div>
                        <small>Goal</small><br>
                        <strong>{goal.capitalize()}</strong>
                    </div>
                    <div>
                        <small>Audience</small><br>
                        <strong>{audience.capitalize()}</strong>
                    </div>
                    <div>
                        <small>Platform</small><br>
                        <strong>{platform.capitalize()}</strong>
                    </div>
                    <div>
                        <small>Style</small><br>
                        <strong>{style.replace('-', ' ').title()}</strong>
                    </div>
                    <div>
                        <small>Tone</small><br>
                        <strong>{tone.capitalize()}</strong>
                    </div>
                </div>
            </div>
        </header>
        
        <div class="card">
            <h3>Your Original Prompt:</h3>
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 3px solid #d1d5db;">
                <p style="margin: 0; color: #4b5563;">"{prompt}"</p>
            </div>
            
            <h3>AI-Optimized Prompt:</h3>
            <div class="document-output" 
                 style="cursor: text; user-select: all; -webkit-user-select: all;"
                 onclick="this.select()">
                
                <div style="padding: 1rem; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 0.9rem; line-height: 1.5;">
                    {optimized_prompt}
                </div>
            </div>
            
            <div style="margin-top: 0.5rem; text-align: center;">
                <small style="color: #666;">
                    <i class="fas fa-mouse-pointer"></i> <strong>Click the prompt above</strong> to select all text, then <strong>Ctrl+C</strong> to copy
                </small>
            </div>
            
            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;">
                <p style="font-weight: 600; color: #374151; margin-bottom: 0.75rem;">How to use this prompt:</p>
                <ol style="margin: 0; padding-left: 1.5rem; color: #4b5563;">
                    <li style="margin-bottom: 0.5rem;"><strong>Click</strong> the prompt above (it will auto-select)</li>
                    <li style="margin-bottom: 0.5rem;"><strong>Copy</strong> with Ctrl+C (Cmd+C on Mac)</li>
                    <li style="margin-bottom: 0.5rem;"><strong>Paste</strong> into {platform.capitalize()} and press enter</li>
                    <li>Get better, more structured results!</li>
                </ol>
            </div>
        </div>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 3rem;">
            <a href="/prompt-wizard/step/1" class="primary" style="text-align: center; padding: 1rem;">
                <i class="fas fa-redo"></i> Create Another Prompt
            </a>
            
            <a href="/" class="secondary" style="text-align: center; padding: 1rem;">
                <i class="fas fa-home"></i> Back to Home
            </a>
        </div>
    </article>
    '''
    
    return layout("Generated Prompt", content, step=7)

print("🟢 3. Reached end of file...")
