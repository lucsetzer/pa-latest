import os

template_dir = os.path.join(os.path.dirname(__file__), "dashboard", "templates")
print("Template directory:", os.path.abspath(template_dir))

# Check if template exists
intro_path = os.path.join(template_dir, "prompt_wizard_intro.html")
print("Intro template exists:", os.path.exists(intro_path))
