# document_wizard/app.py - DOCUMENT WIZARD
from fastapi import FastAPI, Query, Form
from fastapi.responses import HTMLResponse
import uvicorn
import requests
import re
import os

# Detect if running locally or deployed
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") == "production"
# OR: IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"app = FastAPI()

app = FastAPI()
DEEPSEEK_KEY = "sk-d4294fb0fbfc4a56af3050ac660252c2"
            
                
def layout(title: str, content: str) -> str:
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{ --primary: #8b5cf6; }}
        nav {{ margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <!-- SIMPLE NAV - JUST LINKS -->
    <nav class="container">
        <ul>
            <li><strong><a href="/" style="text-decoration:none;">🏠 Home</a></strong></li>
        </ul>
        <ul>
            <li><a href="/prompt-wizard/">✨ Prompt</a></li>
            <li><a href="/thumbnail-wizard/">🖼️ Thumbnail</a></li>
            <li><a href="/video-wizard/">🎬 Video</a></li>
            <li><a href="/hook-wizard/">🎣 Hook</a></li>
            <li><a href="/document-wizard/">📄 Document</a></li>
            <li><a href="#pricing">💰 Pricing</a></li>
        </ul>
    </nav>
    
    <main class="container">
        {content}
    </main>
</body>
</html>'''

# ========== DASHBOARD ==========
@app.get("/")
async def home():
    content = '''
    <div style="text-align: center; padding: 4rem 0;">
        <h1 style="color: var(--primary);">
            <i class="fas fa-file-contract"></i><br>
            Document Decoder
        </h1>
        <p style="font-size: 1.25rem; color: #6b7280; max-width: 600px; margin: 1rem auto;">
            AI-powered translation of complex documents. Understand legal, medical, and technical language in plain English.
        </p>
        
        <div style="margin: 3rem 0;">
            <a href="/wizard" role="button" style="padding: 1rem 2.5rem; font-size: 1.25rem;">
                <i class="fas fa-magic"></i> Decode a Document
            </a>
        </div>
        
        <div class="card-grid">
            <div class="step-card">
                <i class="fas fa-gavel"></i>
                <h3>Legal Documents</h3>
                <p>Contracts, leases, terms of service</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-heart-pulse"></i>
                <h3>Medical Papers</h3>
                <p>Reports, prescriptions, instructions</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-file-signature"></i>
                <h3>Contracts</h3>
                <p>Employment, service, rental agreements</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-warning"></i>
                <h3>Warning Labels</h3>
                <p>Safety instructions, disclaimers</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-graduation-cap"></i>
                <h3>Academic Papers</h3>
                <p>Research, studies, technical docs</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-building"></i>
                <h3>Government Forms</h3>
                <p>Applications, permits, official docs</p>
            </div>
        </div>
        
        <div class="warning-box" style="max-width: 600px; margin: 3rem auto;">
            <h3 style="color: #d97706; margin-top: 0;">
                <i class="fas fa-exclamation-triangle"></i> Important Notice
            </h3>
            <p style="margin-bottom: 0;">
                This tool provides AI-assisted interpretation for educational purposes only. 
                For legal, medical, or financial decisions, always consult a qualified professional.
            </p>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Home", content))

# ========== STEP 1: DOCUMENT TYPE ==========
@app.get("/wizard")
async def step1():
    content = '''
    <div style="max-width: 800px; margin: 0 auto;">
        <div class="steps">
            <div class="step active">1</div>
            <div class="step">2</div>
            <div class="step">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 1: Document Type</h1>
        <p style="text-align: center; color: #6b7280;">
            What type of document are you trying to understand?
        </p>
        
        <div class="card-grid">
            <a href="/wizard/step2?doc_type=legal" class="step-card">
                <i class="fas fa-gavel"></i>
                <h3>Legal Document</h3>
                <p>Contract, lease, terms of service, agreement</p>
            </a>
            
            <a href="/wizard/step2?doc_type=medical" class="step-card">
                <i class="fas fa-heart-pulse"></i>
                <h3>Medical Document</h3>
                <p>Report, prescription, diagnosis, instructions</p>
            </a>
            
            <a href="/wizard/step2?doc_type=contract" class="step-card">
                <i class="fas fa-file-signature"></i>
                <h3>Contract/Agreement</h3>
                <p>Employment, service, rental, purchase agreement</p>
            </a>
            
            <a href="/wizard/step2?doc_type=financial" class="step-card">
                <i class="fas fa-money-bill-wave"></i>
                <h3>Financial Document</h3>
                <p>Loan terms, investment, insurance, tax forms</p>
            </a>
            
            <a href="/wizard/step2?doc_type=technical" class="step-card">
                <i class="fas fa-cogs"></i>
                <h3>Technical Manual</h3>
                <p>Instructions, specifications, warranty</p>
            </a>
            
            <a href="/wizard/step2?doc_type=government" class="step-card">
                <i class="fas fa-landmark"></i>
                <h3>Government Form</h3>
                <p>Application, permit, official document</p>
            </a>
            
            <a href="/wizard/step2?doc_type=academic" class="step-card">
                <i class="fas fa-graduation-cap"></i>
                <h3>Academic Paper</h3>
                <p>Research, study, scientific paper</p>
            </a>
            
            <a href="/wizard/step2?doc_type=other" class="step-card">
                <i class="fas fa-file-alt"></i>
                <h3>Other Complex Document</h3>
                <p>Any difficult-to-understand text</p>
            </a>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/" role="button" class="secondary">Cancel</a>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Step 1: Document Type", content))

# ========== STEP 2: AUDIENCE LEVEL ==========
@app.get("/wizard/step2")
async def step2(doc_type: str = Query("legal")):
    doc_type_names = {
        "legal": "Legal Document",
        "medical": "Medical Document", 
        "contract": "Contract/Agreement",
        "financial": "Financial Document",
        "technical": "Technical Manual",
        "government": "Government Form",
        "academic": "Academic Paper",
        "other": "Complex Document"
    }
    
    content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
        <div class="steps">
            <div class="step">1</div>
            <div class="step active">2</div>
            <div class="step">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 2: Your Knowledge Level</h1>
        <p style="text-align: center; color: #6b7280;">
            How familiar are you with {doc_type_names[doc_type].lower()}s?
        </p>
        
        <p style="text-align: center;"><strong>Document Type:</strong> {doc_type_names[doc_type]}</p>
        
        <div class="card-grid">
            <a href="/wizard/step3?doc_type={doc_type}&level=novice" class="step-card">
                <i class="fas fa-seedling"></i>
                <h3>Novice</h3>
                <p>Little to no experience. Explain like I'm new.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=general" class="step-card">
                <i class="fas fa-user"></i>
                <h3>General Public</h3>
                <p>Basic understanding. Use everyday language.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=educated" class="step-card">
                <i class="fas fa-user-graduate"></i>
                <h3>Educated Layperson</h3>
                <p>Some background. Can handle some terminology.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=professional" class="step-card">
                <i class="fas fa-briefcase"></i>
                <h3>Related Professional</h3>
                <p>Work in related field. Want deeper analysis.</p>
            </a>
        </div>
        
        <div class="info-box">
            <p style="margin: 0;">
                <strong>Tip:</strong> Choose "Novice" for maximum plain English translation. 
                The AI will avoid all jargon and use simple analogies.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/wizard" role="button" class="secondary">Back</a>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Step 2: Knowledge Level", content))

# ========== STEP 3: DOCUMENT INPUT ==========
@app.get("/wizard/step3")
async def step3(
    doc_type: str = Query("legal"),
    level: str = Query("novice")
):
    doc_type_names = {
        "legal": "Legal Document",
        "medical": "Medical Document",
        "contract": "Contract/Agreement", 
        "financial": "Financial Document",
        "technical": "Technical Manual",
        "government": "Government Form",
        "academic": "Academic Paper",
        "other": "Complex Document"
    }
    
    level_names = {
        "novice": "Novice",
        "general": "General Public", 
        "educated": "Educated Layperson",
        "professional": "Related Professional"
    }
    
    content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
        <div class="steps">
            <div class="step">1</div>
            <div class="step">2</div>
            <div class="step active">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 3: Paste Your Document</h1>
        <p style="text-align: center; color: #6b7280;">
            Copy and paste the text you want to understand
        </p>
        
        <div style="background: #f9fafb; padding: 1.5rem; border-radius: 0.75rem; margin: 2rem 0;">
            <h3>Your Selections:</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1rem 0;">
                <div><strong>Document Type:</strong><br>{doc_type_names[doc_type]}</div>
                <div><strong>Your Level:</strong><br>{level_names[level]}</div>
            </div>
        </div>
        
        <div class="warning-box">
            <h4 style="color: #d97706; margin-top: 0;">
                <i class="fas fa-shield-alt"></i> Privacy & Security
            </h4>
            <p style="margin-bottom: 0;">
                • Your document is processed securely via API<br>
                • No data is stored permanently<br>
                • Remove sensitive personal information before pasting<br>
                • For highly confidential documents, use generic examples
            </p>
        </div>
        
        <form action="/process" method="POST">
            <input type="hidden" name="doc_type" value="{doc_type}">
            <input type="hidden" name="level" value="{level}">
            
            <div style="margin: 2rem 0;">
                <label for="document_text">
                    <strong>Document Text:</strong>
                    <p style="color: #6b7280; margin: 0.5rem 0;">
                        Paste the full document or the specific section you want decoded.
                    </p>
                </label>
                <textarea id="document_text" name="document_text" rows="12" 
                          placeholder="Paste your legal clause, medical report, contract section, or any complex text here..."
                          class="doc-input"></textarea>
            </div>
            
            <div style="margin: 2rem 0;">
                <label for="specific_questions">
                    <strong>Specific Questions (Optional):</strong>
                    <p style="color: #6b7280; margin: 0.5rem 0;">
                        What specifically do you want to understand about this document?
                    </p>
                </label>
                <textarea id="specific_questions" name="specific_questions" rows="4" 
                          placeholder="Example questions: 
• What are the hidden risks in this clause?
• What does this medical term mean for my treatment?
• What am I really agreeing to here?
• What are my rights vs. responsibilities?"
                          style="width: 100%; padding: 1rem; border: 2px solid #e5e7eb; border-radius: 0.5rem;"></textarea>
            </div>
            
            <div style="text-align: center; margin: 2rem 0;">
                <button type="submit" style="padding: 1rem 3rem; font-size: 1.2rem;">
                    <i class="fas fa-search"></i> Decode This Document
                </button>
                <p style="margin-top: 1rem; color: #6b7280;">
                    <i class="fas fa-clock"></i> AI analysis takes 15-30 seconds
                </p>
            </div>
        </form>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/wizard/step2?doc_type={doc_type}" role="button" class="secondary">Back</a>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Step 3: Document Input", content))

# ========== PROCESS ==========
@app.post("/process")
async def process_document(
    doc_type: str = Form(...),
    level: str = Form(...),
    document_text: str = Form(...),
    specific_questions: str = Form("")
):
    loading_content = f'''
    <div style="max-width: 800px; margin: 0 auto; text-align: center; padding: 4rem 0;">
        <div style="font-size: 4rem; color: var(--primary); margin-bottom: 2rem;">
            <i class="fas fa-search"></i>
        </div>
        
        <h1 style="color: var(--primary);">Decoding Your Document...</h1>
        <p style="font-size: 1.2rem; color: #6b7280; max-width: 500px; margin: 1rem auto;">
            Analyzing {doc_type.replace("_", " ").title()} text for a {level} understanding...
        </p>
        
        <div class="loading-bar">
            <div class="loading-progress"></div>
        </div>
        
        <p style="color: #6b7280; margin-top: 2rem;">
            <i class="fas fa-lightbulb"></i> Looking for tricky language, hidden meanings, and plain English translations...
        </p>
        
        <meta http-equiv="refresh" content="3;url=/result?doc_type={doc_type}&level={level}&document_text={document_text}&specific_questions={specific_questions}">
    </div>
    '''
    
    return HTMLResponse(layout("Decoding...", loading_content))

# ========== RESULT ==========
# ========== RESULT ==========
@app.get("/result")
async def show_result(
    doc_type: str = Query(...),
    level: str = Query(...),
    document_text: str = Query(...),
    specific_questions: str = Query("")
):
    # YOUR TURQUOISE COLOR
    TURQUOISE = "#0d96c1"
    TURQUOISE_LIGHT = "#ecfeff"
    TURQUOISE_DARK = "#0c4a6e"
    
    # CHECK DOCUMENT SIZE FIRST
    word_count = len(document_text.split())
    
    if word_count > 2000:
        result_content = f'''
<div style="max-width: 800px; margin: 0 auto; text-align: center;">
    <h1 style="color: #d97706;"><i class="fas fa-exclamation-triangle"></i> Document Too Large</h1>
    <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0;">
        <p><strong>{word_count} words detected (limit: 2,000 words)</strong></p>
        <p>For best results:</p>
        <ol style="text-align: left; max-width: 500px; margin: 1rem auto;">
            <li><strong>Extract the most important section</strong> (1-2 paragraphs)</li>
            <li>Focus on the <strong>specific clause</strong> you don't understand</li>
            <li>Copy just the <strong>key paragraphs</strong></li>
        </ol>
    </div>
    <div style="margin: 2rem 0;">
        <a href="/wizard/step3?doc_type={doc_type}&level={level}" 
           role="button" style="background: {TURQUOISE}; border-color: {TURQUOISE};">
            <i class="fas fa-edit"></i> Try Again with Smaller Section
        </a>
    </div>
</div>
'''
        return HTMLResponse(layout("Document Too Large", result_content))
    
    # TEST MODE
    TEST_MODE = False
    
    try:
    if TEST_MODE:
        ai_text = '''...test data...'''
    else:
        ai_text = "Real API mode - set TEST_MODE = False"
    
    # ... all your parsing and HTML building ...
    
    result_content = f'''
<div style="max-width: 800px; margin: 0 auto;">
    ... your beautiful analysis HTML ...
    {analysis_html}
</div>
'''
    
    # SUCCESS RETURN - INSIDE TRY BLOCK
    return HTMLResponse(layout("Document Analysis Results", result_content))
    
except Exception as e:
    # Error return
    result_content = f'''...error HTML...'''
    return HTMLResponse(layout("Document Analysis Results", result_content))
    
PLAIN ENGLISH TRANSLATION:
This section says: "If someone sues the other party for any reason, the first party will pay for all legal costs and damages." 
• You're agreeing to cover ALL legal expenses if the other party gets sued
• This applies even if the lawsuit isn't really their fault
• There's no limit to how much you might have to pay

TRICKY LANGUAGE ALERT:
• "Indemnifies and holds harmless": Means you'll pay ALL legal costs for the other party | This is very broad protection for them | Example: If they get sued for $1M, you pay it
• "Any and all claims, demands, damages": Means EVERY possible type of legal complaint | Very broad language that covers things you can't predict | Example: Future lawsuits you can't imagine today
• "Causes of action or suits at law or in equity": Means ANY type of lawsuit in ANY court system | Covers more than just normal lawsuits | Example: Arbitration, mediation, court cases

RED FLAGS TO WATCH FOR:
• Unlimited liability: You could owe millions with no cap | Very risky for individuals/small businesses | Ask for: A dollar limit or "to the extent permitted by law"
• One-sided protection: Only protects the other party, not you | Creates unequal relationship | Ask for: Mutual indemnification (both sides protect each other)
• Broad language: "Any and all" means literally everything | Could cover lawsuits unrelated to your actual work | Ask for: Specific list of what's covered

STANDARD/BOILERPLATE SECTIONS:
• Legal jurisdiction: Which state's laws apply | Most contracts have this | No need to worry unless it's an unusual state
• Notice provisions: How to send official letters | Standard administrative detail | Just note the addresses/email
• Severability: If one part is illegal, rest stays valid | Standard protection for both sides | Nothing to negotiate

YOUR RIGHTS (What you can do):
• Right to receive notice: They must notify you before suing | How to exercise: Make sure your contact info is correct
• Right to defend: You can choose the lawyers (usually) | How to exercise: Ask for "right to select counsel" in clause

YOUR RESPONSIBILITIES (What you must do):
• Pay all legal costs: You cover everything if they get sued | Consequences if not done: They can sue you for reimbursement
• Cooperate with defense: You must help with the legal case | Consequences if not done: Could lose insurance coverage

NEXT STEPS & QUESTIONS TO ASK:
1. Question to ask a lawyer: "Is there a way to cap my liability at a specific dollar amount or my insurance limits?"
2. Action to take: Ask for "mutual indemnification" - both sides protect each other equally
3. What to research: Your insurance policy - does it cover "contractual liability"?

BOTTOM LINE SUMMARY:
This is a very one-sided liability clause that could leave you responsible for unlimited legal costs if the other party gets sued for any reason. For a novice, this is risky without a liability cap. Ask for either a dollar limit or make it mutual so both sides have the same protection.'''
        else:
            ai_text = "Real API mode - set TEST_MODE = False"
        
        # Parse sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in ai_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.endswith(':'):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.rstrip(':')
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Build cards - SIMPLE VERSION THAT WON'T BREAK
        analysis_html = ""
        
        section_config = [
            ("PLAIN ENGLISH TRANSLATION", "fa-language", "The document in simple terms"),
            ("TRICKY LANGUAGE ALERT", "fa-exclamation-triangle", "Watch out for these terms"),
            ("RED FLAGS TO WATCH FOR", "fa-flag", "Potential concerns to address"),
            ("STANDARD/BOILERPLATE SECTIONS", "fa-check-circle", "Normal sections, nothing to worry"),
            ("YOUR RIGHTS", "fa-shield-alt", "What you're entitled to"),
            ("YOUR RESPONSIBILITIES", "fa-tasks", "What you need to do"),
            ("NEXT STEPS & QUESTIONS TO ASK", "fa-question-circle", "Actionable advice"),
            ("BOTTOM LINE SUMMARY", "fa-bullseye", "The most important takeaway")
        ]
        
        for section_title, icon, description in section_config:
            if section_title in sections:
                content = sections[section_title]
                
                analysis_html += f'''
<div style="background: white; border: 2px solid {TURQUOISE}; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; display: block;">
    <h3 style="color: {TURQUOISE}; margin-top: 0; border-bottom: 2px solid {TURQUOISE_LIGHT}; padding-bottom: 0.5rem;">
        <i class="fas {icon}" style="margin-right: 0.5rem;"></i>{section_title}
    </h3>
    <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">
        <i class="fas fa-info-circle"></i> {description}
    </p>
    <div style="background: {TURQUOISE_LIGHT}; padding: 1rem; border-radius: 8px; border-left: 4px solid {TURQUOISE}; color: {TURQUOISE_DARK}; line-height: 1.6;">
        {content.replace(chr(10), '<br>').replace('•', '•')}
    </div>
</div>
'''
        
        # Score card
        if "OVERALL COMPLEXITY SCORE" in ai_text:
            score = "5"
            try:
                import re
                score_match = re.search(r'(\d+(?:\.\d+)?)/10', ai_text)
                if score_match:
                    score = score_match.group(1)
            except:
                pass
            
            try:
                score_num = float(score)
                if score_num >= 8:
                    score_color = "#dc2626"
                    score_icon = "fa-brain"
                    score_text = "Very Complex"
                elif score_num >= 6:
                    score_color = "#d97706"
                    score_icon = "fa-exclamation-triangle"
                    score_text = "Complex"
                elif score_num >= 4:
                    score_color = TURQUOISE
                    score_icon = "fa-balance-scale"
                    score_text = "Moderate"
                else:
                    score_color = "#059669"
                    score_icon = "fa-check-circle"
                    score_text = "Fairly Simple"
            except:
                score_color = TURQUOISE
                score_icon = "fa-file-alt"
                score_text = "Document Analysis"
            
            score_html = f'''
<div style="background: white; border: 3px solid {score_color}; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; text-align: center; display: block;">
    <div style="font-size: 0.9rem; color: {score_color}; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">
        <i class="fas {score_icon}"></i> Document Complexity Score
    </div>
    <div style="font-size: 4rem; font-weight: bold; color: {score_color}; margin: 0.5rem 0; line-height: 1;">
        {score}<span style="font-size: 2rem; opacity: 0.7;">/10</span>
    </div>
    <div style="font-size: 1.1rem; color: #374151; margin-top: 0.5rem;">
        {score_text} • {doc_type.replace("_", " ").title()} • {level.replace("_", " ").title()} Level
    </div>
</div>
'''
            analysis_html = score_html + analysis_html
        
        result_content = f'''
<div style="max-width: 800px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 3rem; color: {TURQUOISE};">
            <i class="fas fa-file-contract"></i>
        </div>
        <h1 style="color: {TURQUOISE};">Document Decoded!</h1>
        <p style="color: #64748b;">Translated for <strong>{level.replace("_", " ").title()}</strong> understanding</p>
    </div>
    
    <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0;">
        <h4 style="color: #d97706; margin-top: 0;">
            <i class="fas fa-gavel"></i> Legal Disclaimer
        </h4>
        <p style="margin-bottom: 0;">
            This AI analysis is for educational purposes only. It helps you understand documents better, 
            but is NOT legal, medical, or financial advice. For important decisions, consult a qualified professional.
        </p>
    </div>
    
    {analysis_html}
    
    <div style="text-align: center; margin-top: 3rem;">
        <a href="/wizard" role="button" style="margin-right: 1rem; background: {TURQUOISE}; border-color: {TURQUOISE};">
            <i class="fas fa-file-contract"></i> Decode Another Document
        </a>
        <a href="/" role="button" style="background: #64748b; border-color: #64748b;">
            <i class="fas fa-home"></i> Dashboard
        </a>
    </div>
</div>
'''
    
    except Exception as e:
        result_content = f'''
<div style="max-width: 800px; margin: 0 auto; text-align: center;">
    <h1 style="color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> Analysis Error</h1>
    <p>{str(e)}</p>
    <a href="/wizard/step3?doc_type={doc_type}&level={level}" 
       role="button" style="margin-top: 2rem; background: {TURQUOISE}; border-color: {TURQUOISE};">Try Again</a>
</div>
'''
    
    return HTMLResponse(layout("Document Analysis Results", result_content))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
