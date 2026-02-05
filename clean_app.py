# clean_app.py
from fastapi import FastAPI, Request, Cookie, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from shared.auth import verify_magic_link
from dotenv import load_dotenv
from requests.exceptions import Timeout, ConnectionError
import requests
import os
import html
import re

app = FastAPI()
template_dir = os.path.join(os.path.dirname(__file__), "dashboard", "templates")
templates = Jinja2Templates(directory=template_dir)

load_dotenv()

# ==================== PROMPT WIZARD ROUTES BEGIN ====================

def call_deepseek_for_prompt(goal, audience, depth, style, tone, user_prompt):
    """Call DeepSeek API to generate a direct answer based on wizard parameters."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "## Error: DeepSeek API key not configured"
    
    system_prompt = f"""You are an expert AI assistant. Generate a polished, ready‑to‑use answer based on the user's request and the following specifications:

- Goal: {goal}
- Target audience: {audience}
- Desired depth: {depth}
- Preferred style: {style}
- Desired tone: {tone}

CRITICAL FORMATTING RULES:
1. **Start with a one‑sentence summary** of the answer.
2. Use **short paragraphs** (max 3 sentences each).
3. For code or examples, provide a **brief explanation first**, then put the code in a distinct block.
4. Use **bullet points** or **numbered steps** for any list or sequence.
5. End with **2‑3 key takeaways** (concise, actionable).
6. Avoid walls of text; keep sections visually distinct with clear line breaks.
7. Match the tone ({tone}) and tailor complexity for {audience}.

- If the request involves a lecture, workshop, or tutorial:
  * Provide a clear timeline (e.g., "0‑5 min: Introduction", "5‑15 min: Basics").
  * Separate each major concept into its own section with a heading.
  * Include 2‑3 code examples with line‑by‑line explanations.
  * Add 1‑2 interactive exercises or questions for the audience.
  * Conclude with a summary and suggested next steps.
- For "expert" depth, include advanced tips, common pitfalls, and best practices.

IMPORTANT:
- Provide a complete, self‑contained answer — do NOT output a meta‑prompt or instructions.
- Structure the answer appropriately for the specified style ({style}).
- Only provide code examples if the user’s request specifically asks for code, programming, or technical implementation.
- For non‑technical topics (e.g., animal training, writing, planning), use plain English instructions, bullet points, or step‑by‑step guides without pseudocode.
- If depth is "comprehensive" or "expert", include examples, steps, or citations as needed.
- Do not add any introductory or concluding meta‑commentary."""

    user_message = f"""Original request: "{user_prompt}"

Generate a detailed, comprehensive answer suitable for a {depth}-level audience. 
- If this is a lecture or tutorial, provide a full session outline with timing, examples, and exercises.
- Be thorough and instructional; do not skip steps.
- Aim for approximately 1000‑1500 words if depth is 'expert' or 'comprehensive'.

Final answer:"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 2500
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=45
        )
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"## API Error {response.status_code}\n{response.text}"
    except Exception as e:
        return f"## Error: {str(e)}"

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
    
        # Depth levels (Step 3)
    "quick": "fa-solid fa-bolt",
    "balanced": "fa-solid fa-scale-balanced",
    "comprehensive": "fa-solid fa-book",
    "expert": "fa-solid fa-microscope",
    
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

def format_ai_output(raw_text):
    """Convert basic Markdown and code fences to HTML."""
    if not raw_text:
        return ""
    
    # 1. Escape HTML entities
    text = html.escape(raw_text)
    
    # 2. Convert code fences
    def replace_code(match):
        lang = match.group(1) or ""
        code = match.group(2)
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    
    text = re.sub(r'```(\w*)\n(.*?)```', replace_code, text, flags=re.DOTALL)
    
    # 3. Convert headings (## → h3, ### → h4)
    text = re.sub(r'^### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # 4. Convert line breaks (two newlines → <br><br>)
    text = text.replace('\n\n', '<br><br>')
    
    return text

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

print("=" * 60)
print("✅ ROUTES REGISTERED:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"  {route.path}")
print("=" * 60)

@app.get("/prompt-wizard/generate", response_class=HTMLResponse)
async def generate_optimized_prompt(
    request: Request,
    goal: str,
    audience: str,
    depth: str,      
    style: str,
    tone: str,
    prompt: str,
    session: str = Cookie(default=None)
):
    """Generate the final optimized prompt"""
    # Auth
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/generate?goal={goal}&audience={audience}&platform={platform}&style={style}&tone={tone}&prompt={prompt}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

    # TODO: Add token check/deduction here (optional for now)

    # Call DeepSeek
    optimized = call_deepseek_for_prompt(goal, audience, depth, style, tone, prompt)

    # Result page
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1><i class="fas fa-check-circle" style="color: var(--primary);"></i> Prompt Ready!</h1>
                <p>Your AI‑optimized prompt for {depth.replace('-', ' ').title()}</p>
            </hgroup>
            
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
                        <strong>{depth.replace('-', ' ').title()}</strong>
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
            
            <h3>AI‑Optimized Prompt:</h3>
                        <div class="prompt-output" ... >
                {format_ai_output(optimized)}
            </div>

            <!-- Copy button -->
            <div style="text-align: center; margin-top: 1rem;">
                <button class="copy-button" onclick="copyAnswer()" style="padding: 0.5rem 1.5rem;">
                    <i class="fas fa-copy"></i> Copy Answer
                </button>
                <span id="copy-feedback" style="margin-left: 0.75rem; color: #0cc0df; display: none;">
                    <i class="fas fa-check"></i> Copied!
                </span>
            </div>
            
            <div style="margin-top: 1.5rem; ...">
            
            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;">
                <p style="font-weight: 600; color: #374151; margin-bottom: 0.75rem;">How to use:</p>
                <ol style="margin: 0; padding-left: 1.5rem; color: #4b5563;">
                    <li style="margin-bottom: 0.5rem;"><strong>Click</strong> the prompt above (it will auto‑select)</li>
                    <li style="margin-bottom: 0.5rem;"><strong>Copy</strong> with Ctrl+C (Cmd+C on Mac)</li>
                    <li style="margin-bottom: 0.5rem;"><strong>Paste</strong> into {depth.replace('-', ' ').title()} and press enter</li>
                    <li>Get better, more structured results!</li>
                </ol>
            </div>
        </div>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 3rem;">
            <a href="/prompt-wizard/step/1" class="primary" style="text-align: center; padding: 1rem;">
                <i class="fas fa-redo"></i> Create Another Prompt
            </a>
            <a href="/dashboard" class="secondary" style="text-align: center; padding: 1rem;">
                <i class="fas fa-home"></i> Back to Dashboard
            </a>
        </div>
        
        <script>
        function copyAnswer() {{
            const answerElement = document.querySelector('.prompt-output');
            const text = answerElement.textContent;
            
            navigator.clipboard.writeText(text).then(() => {{
                const feedback = document.getElementById('copy-feedback');
                feedback.style.display = 'inline';
                setTimeout(() => {{
                    feedback.style.display = 'none';
                }}, 2000);
            }}).catch(err => {{
                alert('Copy failed. You can manually select the text and press Ctrl+C.');
            }});
        }}
        </script>
    </article>
    '''

    return layout("Generated Prompt", content)

@app.get("/prompt-wizard/step/1", response_class=HTMLResponse)
async def prompt_wizard_step1(request: Request, session: str = Cookie(default=None)):
    """Step 1: Goal selection with visual cards"""
    # Auth check
    if not session:
        return RedirectResponse("/login?next=/prompt-wizard/step/1")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

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
            <h3>{label}</h3>
            <p>{description}</p>
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
                    <div class="progress-fill" style="width: 16.6% !important;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step active">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Depth</div>
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
            <a href="/dashboard" class="secondary">
                <i class="fas fa-home"></i> Back to Dashboard
            </a>
        </div>
    </article>
    '''

    # Use the layout function you already have in clean_app.py
    return layout("Step 1: Goal Selection", content)



@app.get("/prompt-wizard/step/2", response_class=HTMLResponse)
async def prompt_wizard_step2(request: Request, goal: str = "explain", session: str = Cookie(default=None)):
    """Step 2: Audience selection"""
    # Auth check
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/step/2?goal={goal}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

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
            <h3>{label}</h3>
            <p>{description}</p>
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
                    <div class="progress-fill" style="width: 33% !important;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step active">2. Audience</div>
                    <div class="progress-step">3. Depth</div>
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

    return layout("Step 2: Audience Selection", content)

@app.get("/prompt-wizard/step/3", response_class=HTMLResponse)
async def prompt_wizard_step3(
    request: Request,
    goal: str = "explain",
    audience: str = "general",
    session: str = Cookie(default=None)
):
    """Step 3: Depth/Detail selection"""
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/step/3?goal={goal}&audience={audience}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

    depth_levels = [
        ("quick", "Quick Answer", "Concise, to‑the‑point", "fa-solid fa-bolt"),
        ("balanced", "Balanced", "Clear explanation with examples", "fa-solid fa-scale-balanced"),
        ("comprehensive", "Comprehensive", "Step‑by‑step, includes tips & mistakes", "fa-solid fa-book"),
        ("expert", "Expert Deep Dive", "Advanced techniques, frameworks, citations", "fa-solid fa-microscope"),
    ]

    depth_cards = ""
    for value, label, description, icon in depth_levels:
        depth_cards += f'''
        <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&depth={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon}"></i>
            </div>
            <h3>{label}</h3>
            <p>{description}</p>
        </a>
        '''

    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 3: How detailed do you want the response?</h1>
                <p>Choose the depth of the AI's answer</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 50%;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step active">3. Depth</div>
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
            {depth_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/2?goal={goal}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 2
            </a>
        </div>
    </article>
    '''

    return layout("Step 3: Depth Selection", content)

@app.get("/prompt-wizard/step/4", response_class=HTMLResponse)
async def prompt_wizard_step4(
    request: Request,
    goal: str = "explain",
    audience: str = "general",
    depth: str = "balanced",   # new parameter
    session: str = Cookie(default=None)
):
    """Step 4: Style selection"""
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/step/4?goal={goal}&audience={audience}&depth={depth}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

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
        <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&depth={depth}&style={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3>{label}</h3>
            <p>{description}</p>
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
                    <div class="progress-fill" style="width: 66% !important;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Depth</div>
                    <div class="progress-step active">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} (Depth: {depth.replace('-', ' ').title()})</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {style_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/3?goal={goal}&audience={audience}&depth={depth}" ... >
                <i class="fas fa-arrow-left"></i> Back to Step 3
            </a>
        </div>
    </article>
    '''

    return layout("Step 4: Style Selection", content)

@app.get("/prompt-wizard/step/5", response_class=HTMLResponse)
async def prompt_wizard_step5(
    request: Request,
    goal: str = "explain",
    audience: str = "general",
    depth: str = "balanced",
    style: str = "direct",
    session: str = Cookie(default=None)
):
    """Step 5: Tone selection"""
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/step/5?goal={goal}&audience={audience}&depth={depth}&style={style}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

    tones = [
        ("professional", "Professional", "Formal, business-appropriate"),
        ("friendly", "Friendly", "Warm, approachable, casual"),
        ("authoritative", "Authoritative", "Confident, expert-like"),
        ("enthusiastic", "Enthusiastic", "Energetic, passionate"),
        ("neutral", "Neutral", "Objective, unbiased"),
        ("humorous", "Humorous", "Funny, lighthearted"),
    ]

    print(f"DEBUG: tones = {tones}")

    tone_cards = ""
    for value, label, description in tones:
        print(f"DEBUG inside loop: {value}, {label}")
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        tone_cards += f'''
        <a href="/prompt-wizard/step/6?goal={goal}&audience={audience}&depth={depth}&style={style}&tone={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3>{label}</h3>
            <p>{description}</p>
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
                    <div class="progress-fill" style="width: 83% !important;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Depth</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step active">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} (Depth: {depth.replace('-', ' ').title()}) in {style.replace('-', ' ').title()} style</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {tone_cards}
        </div>
        
        

        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&depth={depth}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 4
            </a>
        </div>
    </article>
    '''

    return layout("Step 5: Tone Selection", content)

@app.get("/prompt-wizard/step/6", response_class=HTMLResponse)
async def prompt_wizard_step6(
    request: Request,
    goal: str = "explain",
    audience: str = "general",
    depth: str = "balanced",    # ← replaced platform with depth
    style: str = "direct",
    tone: str = "professional",
    session: str = Cookie(default=None)
):
    """Step 6: Enter your prompt"""
    if not session:
        return RedirectResponse(f"/login?next=/prompt-wizard/step/6?goal={goal}&audience={audience}&platform={platform}&style={style}&tone={tone}")
    email = verify_magic_link(session, mark_used=False)
    if not email:
        return RedirectResponse("/login")

    # Summary of selections
    selections_html = f'''
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
                <strong>{depth.replace('-', ' ').title()}</strong>
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
                    <div class="progress-fill" style="width: 100% !important;"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Depth</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step active">6. Prompt</div>
                </div>
            </div>
            
            {selections_html}
        </header>
        
        <form action="/prompt-wizard/generate" method="get">
            <!-- Hidden fields to pass selections -->
            <input type="hidden" name="goal" value="{goal}">
            <input type="hidden" name="audience" value="{audience}">
            <input type="hidden" name="depth" value="{depth}">
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
                            <li>Don't worry about perfection – AI will optimize it!</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button type="submit" class="primary" style="padding: 1rem 2rem; font-size: 1.1rem;">
                    <i class="fas fa-magic"></i> Generate Optimized Prompt
                </button>
                
                <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&depth={depth}&style={style}" 
                   class="secondary" style="margin-left: 1rem;">
                    <i class="fas fa-arrow-left"></i> Back
                </a>
            </div>
        </form>
    </article>
    '''

    return layout("Step 6: Enter Your Prompt", content)

def layout(title, content):
    css = """
    <style>
        :root {
            --primary: #0cc0df;
            --primary-hover: #0aa9c3;
            --primary-focus: rgba(12, 192, 223, 0.2);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }

        .step-card {
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: #e2e8f0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
            min-height: 180px;
            justify-content: center;
            
        }
        
        .step-card:hover {
            border-color: var(--primary);
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0, 245, 212, 0.15);
            
        }
        
        .step-card h3 {
            margin: 0;
            color: #ffffff;                /* Bright white for headings */
            font-weight: 600;
        }

        .step-card p {
            margin: 0;
            color: #cbd5e1;                /* Light gray for descriptions */
            font-size: 0.9rem;
        }

        .step-icon {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }
        
        .progress-container {
            margin: 2rem 0;
        }
        
        .progress-bar {
            height: 8px;
            background: #0cc0df;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), #0cc0df);
            transition: width 0.5s ease;
        }
        
        .progress-steps {
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #999;
        }
        
        .progress-step {
            text-align: center;
            flex: 1;
        }
        
        .progress-step.active {
            color: var(--primary);
            font-weight: bold;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        {css}
    </head>
    <body>
        <main class="container">
            {content}
        </main>
    </body>
    </html>
    """

# ==================== PROMPT WIZARD ROUTES END ====================

# 1. Frontpage
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("frontpage.html", {"request": request})

# 2. Login
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login-test")
async def login_test_get():
    """Test login without form"""
    print("🔓 GET /login-test called")
    
    # Simulate what the POST route does
    email = "get-test@example.com"
    
    from shared.email_service import send_magic_link_email
    magic_link = send_magic_link_email(email)
    print(f"🔓 Magic link from GET: {magic_link}")
    
    return {"magic_link": magic_link, "email": email}

@app.post("/login")
async def login_request(email: str = Form(...)):
    print("=" * 60)
    print(f"🎯 LOGIN ROUTE ENTERED - Email: {email}")
    print("=" * 60)
    
    token = None
    
    # STEP 1: Try email service
    print(f"1️⃣ ATTEMPTING EMAIL SERVICE...")
    try:
        print(f"   Importing send_magic_link_email...")
        from shared.email_service import send_magic_link_email
        print(f"   ✅ Import successful")
        print(f"   Calling send_magic_link_email('{email}')...")
        magic_link = send_magic_link_email(email)
        print(f"   ✅ Function returned: {magic_link}")
        
        # Extract token
        if magic_link and "token=" in str(magic_link):
            token = magic_link.split("token=")[-1]
            print(f"   Extracted token: {token[:30]}...")
        else:
            token = magic_link or "unknown"
            print(f"   Using as-is token: {token[:30]}...")
            
    except ImportError as e:
        print(f"   ❌ IMPORT ERROR: {e}")
        token = f"test_{email}"
        print(f"   Created fallback token: {token}")
    except Exception as e:
        print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        token = f"error_{email}"
    
    # STEP 2: Store token
    print(f"\n2️⃣ ATTEMPTING TO STORE TOKEN...")
    if token:
        try:
            print(f"   Importing store_magic_token...")
            from shared.auth import store_magic_token
            print(f"   ✅ Import successful")
            stored = store_magic_token(email, token)
            print(f"   Storage result: {stored}")
        except Exception as e:
            print(f"   ❌ Storage failed: {e}")
    else:
        print(f"   ⚠️ No token to store")
    
    print(f"\n3️⃣ REDIRECTING TO CHECK-EMAIL PAGE")
    print("=" * 60)
    return RedirectResponse(f"/check-email?email={email}", status_code=303)

# 3. Auth
@app.get("/auth")
async def auth_callback(token: str):
    print(f"🔐 AUTH ROUTE - Token: {token[:30]}...")
    
    try:
        
        # Use mark_used=False so dashboard can also verify it
        email = verify_magic_link(token, mark_used=False)
        
        if email:
            print(f"🔐 SUCCESS! Logging in: {email}")
            response = RedirectResponse("/dashboard")
            response.set_cookie(key="session", value=token, httponly=True, secure=False)
            return response
        else:
            print(f"🔐 Token invalid or already used")
            return RedirectResponse("/login?error=invalid_token")
            
    except Exception as e:
        print(f"🔐 ERROR: {e}")
        return RedirectResponse("/login?error=exception")

# 4. Dashboard
@app.get("/dashboard")
async def dashboard(request: Request, session: str = Cookie(default=None)):
    print(f"📊 DASHBOARD - Session cookie: {session[:30] if session else 'NO COOKIE'}")
    if not session:
        return RedirectResponse("/login")
    
    # VERIFY THE SESSION TOKEN TO GET REAL USER EMAIL
    try:
        from shared.auth import verify_magic_link
        # session cookie contains the token
        email = verify_magic_link(session, mark_used=False)
        if not email:
            print(f"❌ Token verification failed")
            return RedirectResponse("/login")
        print(f"✅ Dashboard for: {email}")
    except ImportError as e:
        print(f"⚠️ shared.auth not found: {e}, using test email")
        email = "test@example.com"
    
    # GET REAL BALANCE FROM DATABASE
    try:
        from central_bank import get_balance as get_user_balance
        balance = get_user_balance(email)
        print(f"✅ User balance: {balance} tokens")
    except ImportError as e:
        print(f"⚠️ Balance module not found: {e}")
        balance = 100
    
    # DEBUG: Print apps list
    # In your dashboard function in clean_app.py
    # In clean_app.py, update apps_list:
    apps_list = [
        {"name": "Thumbnail Wizard", "cost": 4, "icon": "🖼️", "status": "ready", 
        "url": "/thumbnail-wizard", "description": "Create thumbnails"},
        
        {"name": "Document Wizard", "cost": 4, "icon": "📄", "status": "ready", 
        "url": "/document-wizard", "description": "Process documents"},
        
        {"name": "Hook Wizard", "cost": 4, "icon": "🎣", "status": "ready", 
        "url": "/hook-wizard", "description": "Create hooks"},
        
        {"name": "Prompt Wizard", "cost": 5, "icon": "✨", "status": "ready", 
        "url": "/prompt-wizard/step/1", "description": "Build AI prompts"},  # ← FIXED!
        
        {"name": "Script Wizard", "cost": 3, "icon": "📝", "status": "ready", 
        "url": "/script-wizard", "description": "Write scripts"},
        
        {"name": "A11y Wizard", "cost": 0, "icon": "♿", "status": "ready", 
        "url": "/a11y-wizard", "description": "Accessibility tools"},
    ]
    
    print(f"📊 Passing {len(apps_list)} apps to template")
    for app in apps_list:
        print(f"  - {app['name']}")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_email": email,
        "balance": balance,
        "apps": apps_list
    })

@app.get("/prompt-wizard")
async def prompt_wizard(request: Request, session: str = Cookie(default=None)):
    """Prompt Wizard main form"""
    print("🎯 /prompt-wizard route hit")
    
    if not session:
        print("  🔀 No session, redirecting to login")
        return RedirectResponse("/login?next=/prompt-wizard")
    
    from shared.auth import verify_magic_link
    email = verify_magic_link(session, mark_used=False)
    if not email:
        print("  🔀 Invalid session, redirecting to login")
        return RedirectResponse("/login")
    
    # Check balance
    try:
        from central_bank import get_user_balance
        balance = get_user_balance(email)
        print(f"  💰 User balance: {balance} tokens")
    except Exception as e:
        print(f"  ⚠️ Balance check failed: {e}")
        balance = 0
    
    print(f"  ✅ Showing form for: {email}")
    return templates.TemplateResponse("prompt_wizard.html", {
        "request": request,
        "user_email": email,
        "balance": balance
    })

@app.get("/settings")
async def settings(request: Request, session: str = Cookie(default=None)):
    if not session:
        return RedirectResponse("/login")
    
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie(key="session")
    return response

@app.get("/check-email")
async def check_email(request: Request, email: str):
    return templates.TemplateResponse("check_email.html", {
        "request": request,
        "email": email
    })

@app.get("/test-email-now")
async def test_email_now():
    """Test email service directly"""
    try:
        from shared.email_service import send_magic_link_email
        result = send_magic_link_email("test-now@example.com")
        return {
            "status": "success",
            "result": result,
            "result_type": type(result).__name__,
            "contains_token": "token=" in str(result)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/test-email-direct")
async def test_email_direct():
    """Test email service without form complications"""
    print("🔍 DIRECT EMAIL TEST STARTING...")
    
    try:
        from shared.email_service import send_magic_link_email
        print("✅ Import successful")
        
        result = send_magic_link_email("direct-test@example.com")
        print(f"✅ Email service returned: {result}")
        
        if result and "token=" in str(result):
            token = result.split("token=")[-1]
            print(f"✅ Token extracted: {token[:30]}...")
            
            # Verify it
            from shared.auth import verify_magic_link
            email = verify_magic_link(token, mark_used=False)
            print(f"✅ Token verifies to: {email}")
        else:
            print(f"⚠️ No token in result: {result}")
            
        return {"result": str(result)[:100]}
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/test-full-flow")
async def test_full_flow():
    """Test the complete auth flow from start to finish"""
    import webbrowser
    
    print("🧪 TESTING FULL FLOW...")
    
    # 1. Create a token
    from shared.auth import create_magic_link
    test_email = "flow-test@example.com"
    token = create_magic_link(test_email)
    
    # 2. Create the auth URL
    auth_url = f"http://localhost:10000/auth?token={token}"
    print(f"🧪 Auth URL: {auth_url}")
    
    # 3. Verify it would work
    from shared.auth import verify_magic_link
    verified = verify_magic_link(token, mark_used=False)
    print(f"🧪 Token verifies to: {verified}")
    
    # 4. Offer to open it
    print(f"🧪 Open this URL in browser: {auth_url}")
    
    return {"auth_url": auth_url, "test_email": test_email}

@app.get("/test-db-persistence")
async def test_db_persistence():
    """Test if database works between requests"""
    import sqlite3
    from shared.auth import get_db_path
    
    db_path = get_db_path()
    print(f"📁 Database path: {db_path}")
    print(f"📁 File exists: {os.path.exists(db_path)}")
    
    # Connect and count
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Count tokens
    c.execute("SELECT COUNT(*) FROM magic_links")
    count = c.fetchone()[0]
    
    # List them
    c.execute("SELECT token, email, used FROM magic_links")
    rows = c.fetchall()
    
    conn.close()
    
    return {
        "db_path": db_path,
        "token_count": count,
        "tokens": [
            {"token": r[0][:30] + "...", "email": r[1], "used": r[2]}
            for r in rows
        ]
    }

# In clean_app.py, add this route (temporarily):
@app.get("/test-ping")
async def test_ping():
    return {"status": "ok", "message": "clean_app.py is working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
