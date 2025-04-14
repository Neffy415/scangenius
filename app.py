import os
import cv2
import pytesseract
from google import genai
from flask import Flask, render_template, request, redirect, url_for, session,flash
import re
import mimetypes
from pdf2image import convert_from_path
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import inspect
from dotenv import load_dotenv
load_dotenv()
# Flask App Initialization
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Required for session handling

# Configure Upload Folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set up Tesseract

# Load Google Gemini API key from environment variables
 # Ensure the API key is stored securely

app.config['SQLALCHEMY_DATABASE_URI']=os.getenv("database")
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

login_manager.login_message_category = "info"  # Optional: change message category

class users(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(40),nullable=False)
    email=db.Column(db.String(40),unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    ats_records = db.relationship('ats', backref='users', lazy=True)
    cover_letters = db.relationship('coverletter', backref='users', lazy=True)
class ats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    Resume=db.Column(db.String(200), nullable=False)
    ats_score=db.Column(db.String(10))
    skill_score=db.Column(db.String(10))
    tech_score=db.Column(db.String(10))
    keyword_score=db.Column(db.String(10))
    industry=db.Column(db.String(10))
    result=db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

class coverletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    style=db.Column(db.String(20))
    cover=db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())



with app.app_context():
    inspector = inspect(db.engine)  # Get database inspector
    existing_tables = inspector.get_table_names()  # List of existing tables

    # Check if required tables exist before creating them
    if not {"users", "ats", "coverletter"}.issubset(set(existing_tables)):
        db.create_all()






@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))


@app.route('/dashboard')
@login_required
def dashboard():
    ats_records = ats.query.filter_by(user_id=current_user.id).order_by(ats.created_at.desc()).all()
    cover_letters = coverletter.query.filter_by(user_id=current_user.id).order_by(coverletter.created_at.desc()).all()
    return render_template('dashboard.html',ats_records=ats_records,cover_letters=cover_letters)


@app.route('/register',methods=['POST','GET'])
def signup():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        if users.query.filter_by(email=email).first():
            flash("User already registered!")
            return redirect(url_for('login'))
        
        new_user=users(email=email,name=name,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        user=users.query.filter_by(email=email).first()
        if not user:
            flash("User NOT REGISTERED!", "danger")
            return redirect(url_for('signup'))
        elif bcrypt.check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect password!","danger")
            return redirect(url_for('login'))
        
    return render_template("login.html")

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_uploaded_file(file):
    """ Saves the uploaded resume file and returns the file path """
    if not file or file.filename == "":
        return None

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    return filepath

def is_image(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    
    if mime_type and mime_type.startswith("image"):
        return True
    return False

# Define PDF to text conversion function
def pdf_to_text(filepath):
    try:
        # Convert PDF to images (higher DPI for better text quality)
        images = convert_from_path(filepath, dpi=300")

        text_list = []  # Store extracted text for each page

        for img in images:
            # Convert image to NumPy array for OpenCV processing
            img_np = np.array(img)

            # Convert to grayscale (improves OCR accuracy)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

            # Apply adaptive thresholding to enhance contrast
            processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # Denoising to reduce background noise
            denoised = cv2.fastNlMeansDenoising(processed, None, 30, 7, 21)

            # Resize to improve OCR readability
            scale_factor = 1.5  # Increase image size by 150%
            height, width = denoised.shape
            resized = cv2.resize(denoised, (int(width * scale_factor), int(height * scale_factor)), interpolation=cv2.INTER_CUBIC)

            # Extract text using Pytesseract
            text = pytesseract.image_to_string(resized, config="--psm 6")  # PSM 6 works best for blocks of text

            text_list.append(text)  # Append extracted text

        return "\n".join(text_list)  # Return full extracted text

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return ""




def extract_text_from_image(filepath):
    """ Extracts text from an uploaded resume image using Tesseract OCR with preprocessing """
    try:
        if is_image(filepath):
            img = cv2.imread(filepath)
            if img is None:
                return None  # Handle file read errors
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply adaptive thresholding to enhance contrast
            processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # Denoising to remove background noise
            denoised = cv2.fastNlMeansDenoising(processed, None, 30, 7, 21)

            # Resize image to improve OCR recognition
            scale_factor = 1.5  # Enlarge by 150%
            height, width = denoised.shape
            resized = cv2.resize(denoised, (int(width * scale_factor), int(height * scale_factor)), interpolation=cv2.INTER_CUBIC)

            # Apply OCR with proper settings
            custom_config = r'--oem 3 --psm 6'  # OEM 3: Default engine, PSM 6: Block of text
            res = pytesseract.image_to_string(resized, config=custom_config)

        else:
            res = pdf_to_text(filepath)  # Handle PDFs separately

        return res

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return ""


def evaluate_resume(extracted_text, job_desc):

   

    """ Calls Google Gemini API to evaluate the resume based on the job title """
   
    # Initialize Google Gemini API Client
    client = genai.Client(api_key=os.getenv("gemini_api"))

    # Construct the dynamic prompt
    prompt = f"""
You are an expert in ATS resume scoring. Given the extracted resume text below, evaluate it for the job title: '{job_desc}'.

### Evaluation Criteria:  
🔹 **ATS Compliance:** Analyze how well the resume is structured for ATS parsing.  
🔹 **Keyword Relevance:** Match the resume's content with important keywords from the job description.  
🔹 **Content Quality:** Assess clarity, industry-specific terminology, and role-specific skills.  

🔹 **Improvement Suggestions:**  
- Use concise bullet points with emojis to make the response engaging.  
- Format suggestions as **"Subheading: Content"** (Example: **"Format: Good"**) instead of separating them into different lines.    
- Keep it structured and professional.  
- Please use emojis to make it look appealing.
- Don't provide suggestions on any kind of formatting.
- Focus only on keywords words and mainly other things.
-Give it in Detailed bullet points.
- Be Consistent in Scoring, when re-uploaded to score the same resume make sure you remember the constant score. DONT CHANGE THE SCORE FOR THE SAME RESUME PLEASE KEEP IT SAME.
- Always analyze deeply and provide atleast more than 8 bullet points.
- Be Vigilant and smart when someone uploads anything else other than an Resume, Say it directly by mentioning "Please Provide a valid Resume".

🔹 **SPECIAL INSTRUCTIONS**  
- Provide an **ATS Score** strictly in this format → **ATS SCORE: 00/100**  
- **Strict Scoring Criteria:**  
  - **0-20** → Completely irrelevant (no matching job title, missing all core skills).  
  - **21-50** → Weak relevance (some matching keywords, but lacks major skills/experience).  
  - **51-70** → Moderate relevance (good match but missing key job-specific skills).  
  - **71-100** → Strong relevance (high keyword match, experience aligns well).  
- **Keyword Density Matters:** A resume missing multiple high-value keywords should receive a significantly lower score.  
- **Penalize Missing Job-Specific Keywords, Experience, and Skills:** If major skills, experience, or industry-specific terms are missing, reflect that in the score.  
- Deliver at least **8+ bullet points** with detailed analysis.  
- Keep the structure professional yet engaging.  
- Use concise bullet points with **emojis** for readability.  
- Format suggestions as **"Subheading: Content"** instead of listing them separately.  
- **Ignore Formatting Issues** and focus purely on **skills, keywords, and content relevance**.  
- If an invalid file is uploaded (not a resume), respond with **"Please provide a valid resume."**  
- **Mention Courses or Certifications** that can help improve the candidate's resume.
-⚡ No introduction—just provide the ATS score directly, actionable feedback. Avoid unnecessary text like "Here's an evaluation for..." and remove '***' from suggestions.
- DOnt't Provide High ATS SCORE FOR IRRELEVENT JOB DESCRIPTION WITH REFERENCE TO THE RESUME, PLEASE BE STRICTER AND PROVIDE LOW SCORES FOR MISSINF KEYWORDS, SKILLS, SECTIONS . ETC
- Inlude atleast 12-15 points and if more the better.

📍 **Roadmap for Skill Gaps & Resume Improvement:**  
- **🔍 Missing Core Job Title:** If the resume lacks the exact job title or industry-related terms, suggest adding a dedicated **"Summary"** or **"Objective"** section with the correct title.  
- **🎯 Industry-Specific Keywords:** Identify and list **at least 5-10 crucial industry-specific keywords** that are missing and must be added.  
- **📜 Certifications & Courses:** Recommend relevant **online certifications or courses** that can bridge the skill gap.  
- **📊 Experience Alignment:** If the work experience isn't aligned, suggest adding **transferable skills** or **rewording project descriptions** to match industry terms.  
- **📈 Quantifiable Achievements:** Advise on including **data-driven results** (e.g., "Increased efficiency by 20%").  
- **📚 Recommended Learning Path:** Provide 2-3 specific **resources or platforms (Udemy, Coursera, LinkedIn Learning, etc.)** to improve missing skills.  

📌 ** PROVIDE THE FOLLOWING SCORES AS WELL , IT"S COMPULSORY OR MUST TO GIVE THE SCORES IN BELOW FORMAT **
-1️⃣ Skill Match Score:
🔹 Formula: (Number of required skills present / Total required skills) * 100
🔹 Purpose: Shows how well the resume aligns with the required skills.
🔹 Example: If 7 out of 10 required skills are present, Skill Match = 70%
🔹  Explain the score provided with detailed explanation in points.
🔹Please use emojis to make it look appealing.

-2️⃣ Technical Strength:
🔹 Formula: (Number of highly relevant technical skills / Total technical skills in job description) * 100
🔹 Purpose: Focuses only on technical skills (programming languages, frameworks, APIs, databases).
🔹 Example: If the job lists 8 technical skills, but the resume has only 4, Technical Strength = 50%.
🔹  Explain the score provided with detailed explanation in points.
🔹Please use emojis to make it look appealing.

-3️⃣ Keyword Optimization Score:
🔹 Formula: (Number of relevant keywords found / Total keywords in job description) * 100
🔹 Purpose: Measures how well the resume matches ATS keyword expectations.
🔹 Example: If the job description has 15 keywords and the resume includes 12, Keyword Optimization = 80%.
🔹  Explain the score provided with detailed explanation in points.
🔹Please use emojis to make it look appealing.

-4️⃣ Industry Relevance Score:
🔹 Formula: (Experience & projects in the field / Expected experience level) * 100
🔹 Purpose: Evaluates if the candidate has relevant work experience or projects in the same field.
🔹 Example: If 3 relevant projects are expected but the resume lists only 2, Industry Relevance = 66%
🔹 Explain the score provided with detailed explanation in points.
🔹Please use emojis to make it look appealing.


📄 **Extracted Resume Text:**  
{extracted_text}

⚡ No introduction—just provide the ATS score directly, actionable feedback. Avoid unnecessary text like "Here's an evaluation for..." and remove '***' from suggestions.
"""





    # Call Google Gemini API
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    print(response)

    return response.text if response else "Error: No response from AI."


def get_score(result_text):
    # More flexible pattern that handles variations in formatting
    match = re.search(r'ATS\s*SCORE\s*:?\s*(\d+)', result_text, re.IGNORECASE)
    ats_score = match.group(1) if match else "0"
    return ats_score

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/atsscore", methods=["GET", "POST"])
@login_required
def upload_file():
    """ Handles the file upload and redirects to result page """
    if request.method == "POST":
        file = request.files.get("resume")
        job_desc = request.form.get("job-desc")  # Default job title if empty

        filepath = save_uploaded_file(file)
        if not filepath:
            return "Error: No file uploaded"

        extracted_text = extract_text_from_image(filepath)
        if not extracted_text:
            return "Error: Could not extract text from image,UPLOAD A VALID RESUME FILE!!"
        #RESULT
        result = evaluate_resume(extracted_text, job_desc)
        result = re.sub(r'\*\*', '', result)
        result = re.sub(r'\*', '', result)

        score = get_score(result)
        
        #SKILL MATCH SCORE - More flexible pattern
        matchs = re.search(r'Skill\s*Match\s*Score\s*:?\s*(\d+)', result, re.IGNORECASE)
        skill_score = matchs.group(1) if matchs else "0"
        session["skill-score"] = skill_score

        #TECHNICAL SKILL SCORE - More flexible pattern
        matchs = re.search(r'Technical\s*Strength\s*:?\s*(\d+)', result, re.IGNORECASE)
        tech_score = matchs.group(1) if matchs else "0"
        session["tech-score"] = tech_score
        
        #KEYWORD OPTIMIZATION SCORE - More flexible pattern
        matchs = re.search(r'Keyword\s*Optimization\s*Score\s*:?\s*(\d+)', result, re.IGNORECASE)
        key_score = matchs.group(1) if matchs else "0"
        session["key-score"] = key_score

        #INDUSTRY RELEVANCE SCORE - More flexible pattern
        matchs = re.search(r'Industry\s*Relevance\s*Score\s*:?\s*(\d+)', result, re.IGNORECASE)
        ind_score = matchs.group(1) if matchs else "0"
        session["ind-score"] = ind_score
        
        # Store result in session and redirect to result page
        session["ats_result"] = result
        session["ats_score"] = score

        new_entry = ats(user_id=current_user.id, Resume=file.filename, ats_score=score, skill_score=skill_score, tech_score=tech_score, keyword_score=key_score, industry=ind_score, result=result)
        db.session.add(new_entry)
        db.session.commit()

        os.remove(filepath)
        return redirect(url_for("result_page"))

    return render_template("index.html")


@app.route("/result")
def result_page():
    """ Displays the ATS evaluation result on a separate clean page """
    result = session.get("ats_result", "No result available")
    score=session.get("ats_score","No score Found")
    skill_score=session.get("skill-score")
    tech_score=session.get("tech-score")
    key_score=session.get("key-score")
    ind_score=session.get("ind-score")
    return render_template("result.html", result=result,score=score,skill_score=skill_score,tech_score=tech_score,key_score=key_score,ind_score=ind_score)

#-----------------------------------------COVER LETTER SECTION----------------------------------------------
def generate_cover_letter(name, email, job_title, job_desc, company, skills, interest, resumetext, cover_style, address, date, hiringmanager, phone, platform,companyAddress,instructions):
    client = genai.Client(api_key="AIzaSyDsBT3m0BCNnu_XXmaJFCrSywwzVXSVVZs")

    prompt = f"""
You are an expert in professional cover letter writing. Generate a **{cover_style} cover letter** tailored for the applicant based on the provided details. The cover letter should be **engaging, job-focused, and ATS-friendly**, ensuring it aligns well with the job description.

---
### **Cover Letter Template:**
📌 **Applicant Details:**
- **Name:** {name}
- **Address:** {address}
- **Phone Number:** {phone}
- **Email:** {email}
- **Date:** {date}

📌 **Job Details:**
- **Hiring Manager:** {hiringmanager}
- **Job Title:** {job_title}
- **Job Desc:** {job_desc}
- **Company Name:** {company}
- **Company Address Placeholder:** {companyAddress}
- **Platform Where Job Was Found:** {platform}

📌 **User's Skills & Experience:**
- **Skills:** {skills}
- **Relevant Projects:** {resumetext}
- **Interest in the Role:** {interest}

📌 ** User's Special Instructions (if any):**
- ** Instructions :** {instructions}
---
### **Instructions:**
- Maintain a **{cover_style} tone** throughout.
- Keep it **structured with engaging paragraphs**.
- Begin with a **strong opening** that grabs attention.
- Highlight **relevant skills, achievements, and experiences** using **compelling storytelling**.
- Make sure to fulfill user's **instructions** if mentioned deliberately.
- Use **keywords from the job description** for ATS optimization.
- End with a **strong call to action** to encourage the employer to proceed with the applicant.
- **Ensure all placeholders (e.g., [Your Name], [Your Email]) are properly replaced with the user inputs.**
- ** Directly put fields like [Your name:] to actual name which is provided in user input and similarly for other fields.
- ** Dont give any Introductions or suggestions at all just generate only the cover letter with the information you have.
-** Dont mention fields like [Your Name]
- 

✍ **Generate a structured, impactful, and personalized cover letter that makes the applicant stand out.** Keep it professional and directly aligned with the job description.
"""

    


    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text if response else "Error: No response from AI."


@app.route('/coverletter',methods=['POST','GET'])
@login_required
def coverletters():
    if request.method=='POST':
        name = request.form.get('Name')
        email = request.form.get('email')
        job_title = request.form.get('Job-title')
        job_desc = request.form.get('Job-Desc')
        company = request.form.get('CompanyName')
        companyaddress=request.form.get('companyAddress')
        skills = request.form.get('Skills')
        interest = request.form.get('interest')
        resume= request.files.get('resume')
        style=request.form.get('style')
        if style == "formal":
            cover_Style = "Formal"
        elif style == "professional":
            cover_Style = "Professional"
        elif style == "casual":
            cover_Style = "Casual"
        else:
            cover_Style = "Default"

        address=request.form.get('address')
        Date=request.form.get('Date')
        Hiring=request.form.get('hiringmanager')
        phone=request.form.get('PhoneNo')
        instructions=request.form.get('instructions')
        platform=request.form.get('platform')
        filepath=save_uploaded_file(resume)

        if not filepath:
            return 'Error File not uploaded or unsupported!'
        
        resumetext=extract_text_from_image(filepath)
        if not resumetext:
            return 'Couldnt! extract resume text! Retry !'
        
        cover=generate_cover_letter(name,email,job_title,job_desc,company,skills,interest,resumetext,cover_Style,address,Date,Hiring,phone,platform,companyaddress,instructions)
        session['CoverLetter']=cover
        session['style']=cover_Style
        coverStyle=session.get('style')

        new_entry=coverletter(user_id=current_user.id,style=coverStyle,cover=cover)
        db.session.add(new_entry)
        db.session.commit()

        os.remove(filepath)
        
        return redirect(url_for('coverresultfn'))
    return render_template('coverletterform.html')

@app.route('/cover')
def coverresultfn():
    coverletter=session.get('CoverLetter','No cover letter generated error!')
    style=session.get('style')
    return render_template('coverresult.html',coverletter=coverletter,style=style)

@app.route('/base')
def base():
    return render_template('base.html')

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")
