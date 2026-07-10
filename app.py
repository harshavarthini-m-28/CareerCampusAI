# app.py
# Career Compass AI — Main Flask Application
# Modules: Auth (1), Profile (2), AI Recommendation (3), History + PDF (4), Rate Limiting (5)

from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash, Response)
from flask_bcrypt import Bcrypt
import mysql.connector
import google.generativeai as genai
import json
import re
import io
from datetime import datetime, timedelta
from config import Config

# ── PDF Import ────────────────────────────────────────────────────
PDF_ENGINE = None
try:
    from xhtml2pdf import pisa
    PDF_ENGINE = 'xhtml2pdf'
except ImportError:
    PDF_ENGINE = None

# ── App Initialization ────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
bcrypt = Bcrypt(app)

# ── Gemini AI Setup ───────────────────────────────────────────────
genai.configure(api_key=Config.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')


# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


def build_career_prompt(profile):
    """Builds a structured prompt for Gemini AI using the user's profile data."""
    prompt = f"""
You are an expert career counselor and education advisor in India.
A student has shared their academic profile with you.
Your task is to provide a detailed, realistic, and encouraging career guidance report.

== STUDENT PROFILE ==
Education Level : {profile.get('education_level', 'Not specified')}
Stream / Branch : {profile.get('stream', 'Not specified')}
Skills          : {profile.get('skills', 'Not specified')}
Interests       : {profile.get('interests', 'Not specified')}
Career Goal     : {profile.get('career_goal', 'Not specified')}

== YOUR TASK ==
Based on the above profile, generate a career guidance report.
You MUST respond ONLY with a valid JSON object.
Do NOT include any text before or after the JSON.
Do NOT use markdown formatting or backticks.

The JSON must follow this exact structure:
{{
  "career_paths": [
    {{
      "title": "Career Path Name",
      "description": "2-3 sentence description of this career path",
      "why_suitable": "Why this suits the student's profile specifically",
      "salary_range": "Expected salary range in India (fresher to 5 years)",
      "growth": "Short/Medium/High"
    }}
  ],
  "required_skills": [
    {{
      "skill": "Skill name",
      "priority": "Must Have / Good to Have",
      "how_to_learn": "Brief suggestion on how to learn this"
    }}
  ],
  "suggested_courses": [
    {{
      "course_name": "Course or Certification name",
      "platform": "Platform name (Coursera, NPTEL, YouTube etc.)",
      "duration": "Approximate duration",
      "free_or_paid": "Free / Paid"
    }}
  ],
  "next_steps": [
    "Specific action step 1",
    "Specific action step 2",
    "Specific action step 3",
    "Specific action step 4",
    "Specific action step 5"
  ],
  "motivational_message": "One powerful, personalized motivational sentence for this student"
}}

Rules:
- Suggest exactly 3 career paths
- Suggest exactly 5 required skills
- Suggest exactly 4 courses
- Give exactly 5 next steps
- Keep the language simple, practical and suitable for Indian students
- Be specific, not generic
"""
    return prompt


def parse_recommendation(saved_row):
    """
    Converts a raw database row from ai_recommendations
    into a clean Python dictionary ready for templates.
    """
    return {
        'id':                   saved_row['id'],
        'created_at':           saved_row['created_at'],
        'motivational_message': saved_row.get('motivational_msg', ''),
        'career_paths':         json.loads(saved_row.get('career_paths')      or '[]'),
        'required_skills':      json.loads(saved_row.get('required_skills')   or '[]'),
        'suggested_courses':    json.loads(saved_row.get('suggested_courses') or '[]'),
        'next_steps':           json.loads(saved_row.get('next_steps')        or '[]'),
    }


# ─────────────────────────────────────────────────────────────────
# MODULE 1 — AUTHENTICATION ROUTES
# ─────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not full_name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered. Please login.', 'warning')
            cursor.close(); conn.close()
            return redirect(url_for('register'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)",
            (full_name, email, hashed)
        )
        conn.commit()
        cursor.close(); conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return redirect(url_for('login'))

        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close(); conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id']    = user['id']
            session['user_name']  = user['full_name']
            session['user_email'] = user['email']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────────────────────────
# MODULE 2 — USER PROFILE ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    if request.method == 'POST':
        education_level = request.form.get('education_level', '').strip()
        stream          = request.form.get('stream', '').strip()
        skills          = request.form.get('skills', '').strip()
        interests       = request.form.get('interests', '').strip()
        career_goal     = request.form.get('career_goal', '').strip()

        if not education_level or not stream:
            flash('Education level and stream are required.', 'danger')
            cursor.close(); conn.close()
            return redirect(url_for('profile'))

        cursor.execute(
            "SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE user_profiles
                SET education_level=%s, stream=%s, skills=%s,
                    interests=%s, career_goal=%s
                WHERE user_id=%s
            """, (education_level, stream, skills,
                  interests, career_goal, user_id))
        else:
            cursor.execute("""
                INSERT INTO user_profiles
                (user_id, education_level, stream, skills, interests, career_goal)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (user_id, education_level, stream,
                  skills, interests, career_goal))

        conn.commit()
        cursor.close(); conn.close()
        flash('Profile saved successfully!', 'success')
        return redirect(url_for('dashboard'))

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template('profile.html', profile=profile_data)


# ─────────────────────────────────────────────────────────────────
# MODULE 3 — GEMINI AI RECOMMENDATION ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route('/recommend')
def recommend():
    # ── Login check ───────────────────────────────────────────
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    # ── MODULE 5: RATE LIMITING ────────────────────────────────
    # Check when this user last generated a recommendation.
    # If it was less than 3 hours ago, block the request.
    cursor.execute(
        "SELECT last_recommendation_at FROM users WHERE id = %s", (user_id,)
    )
    user_row = cursor.fetchone()

    if user_row and user_row['last_recommendation_at'] is not None:
        last_time = user_row['last_recommendation_at']  # datetime from MySQL
        now       = datetime.utcnow()                    # current UTC time
        cooldown  = timedelta(hours=3)                   # 3-hour wait period
        elapsed   = now - last_time                      # time since last generation

        if elapsed < cooldown:
            # Still inside cooldown window — block and show wait time
            remaining     = cooldown - elapsed
            total_seconds = int(remaining.total_seconds())
            hours_left    = total_seconds // 3600
            minutes_left  = (total_seconds % 3600) // 60

            flash(
                f'You recently generated career advice. '
                f'Please wait {hours_left} hour(s) and {minutes_left} minute(s) '
                f'before generating new advice. '
                f'You can still view your existing recommendations below.',
                'warning'
            )
            cursor.close(); conn.close()
            return redirect(url_for('dashboard'))
    # ── END RATE LIMITING ──────────────────────────────────────

    # ── Profile check ─────────────────────────────────────────
    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()

    if not profile_data:
        flash('Please complete your profile before getting recommendations.',
              'warning')
        cursor.close(); conn.close()
        return redirect(url_for('profile'))

    prompt = build_career_prompt(profile_data)

    # ── Call Gemini API ───────────────────────────────────────
    try:
        response      = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$',     '', response_text)
        response_text = response_text.strip()
        ai_data       = json.loads(response_text)

    except json.JSONDecodeError:
        flash('AI response was not in expected format. Please try again.',
              'danger')
        cursor.close(); conn.close()
        return redirect(url_for('dashboard'))

    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"GEMINI FULL ERROR: {error_msg}")
        if 'API_KEY' in error_msg or 'api_key' in error_msg:
            flash('Gemini API key is invalid. Check your .env file.', 'danger')
        elif 'quota' in error_msg.lower():
            flash('Gemini API quota exceeded. Please try again later.',
                  'warning')
        else:
            flash(f'AI service error: {error_msg[:120]}', 'danger')
        cursor.close(); conn.close()
        return redirect(url_for('dashboard'))

    # ── Save recommendation to database ───────────────────────
    try:
        cursor.execute("""
            INSERT INTO ai_recommendations
            (user_id, prompt_used, raw_response,
             career_paths, required_skills, suggested_courses,
             next_steps, motivational_msg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, prompt, response_text,
            json.dumps(ai_data.get('career_paths', [])),
            json.dumps(ai_data.get('required_skills', [])),
            json.dumps(ai_data.get('suggested_courses', [])),
            json.dumps(ai_data.get('next_steps', [])),
            ai_data.get('motivational_message', '')
        ))
        conn.commit()
        new_id = cursor.lastrowid

        # ── MODULE 5: Record the timestamp of this successful generation ──
        # This is what the rate limiter reads on the user's next visit.
        cursor.execute(
            "UPDATE users SET last_recommendation_at = UTC_TIMESTAMP() WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        # ── END RATE LIMITING TIMESTAMP UPDATE ────────────────────────────

    except Exception:
        flash('Error saving recommendation. Please try again.', 'danger')
        cursor.close(); conn.close()
        return redirect(url_for('dashboard'))

    cursor.close(); conn.close()
    return redirect(url_for('view_recommendation', rec_id=new_id))


@app.route('/my-recommendation')
def my_recommendation():
    """Shows the most recent recommendation (quick access from dashboard)."""
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM ai_recommendations
        WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
    """, (session['user_id'],))
    saved = cursor.fetchone()
    cursor.close(); conn.close()

    if not saved:
        flash('No recommendation found. Please generate one first.', 'info')
        return redirect(url_for('dashboard'))

    return redirect(url_for('view_recommendation', rec_id=saved['id']))


# ─────────────────────────────────────────────────────────────────
# MODULE 4 — HISTORY + INDIVIDUAL VIEW + PDF DOWNLOAD
# ─────────────────────────────────────────────────────────────────

@app.route('/history')
def history():
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, motivational_msg, created_at, career_paths
        FROM ai_recommendations
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    all_recs = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()
    cursor.close(); conn.close()

    for rec in all_recs:
        try:
            paths = json.loads(rec.get('career_paths') or '[]')
            rec['top_career'] = paths[0]['title'] if paths else 'Career Advice'
        except (json.JSONDecodeError, KeyError, IndexError):
            rec['top_career'] = 'Career Advice'

    return render_template('history.html',
                           recommendations=all_recs,
                           profile=profile_data,
                           user_name=session['user_name'],
                           total=len(all_recs))


@app.route('/recommendation/<int:rec_id>')
def view_recommendation(rec_id):
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM ai_recommendations
        WHERE id = %s AND user_id = %s
    """, (rec_id, user_id))
    saved = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()
    cursor.close(); conn.close()

    if not saved:
        flash('Recommendation not found.', 'warning')
        return redirect(url_for('history'))

    ai_data = parse_recommendation(saved)

    return render_template('recommendation.html',
                           ai_data=ai_data,
                           profile=profile_data,
                           user_name=session['user_name'],
                           generated_at=saved['created_at'],
                           rec_id=rec_id)


@app.route('/download-pdf/<int:rec_id>')
def download_pdf(rec_id):
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    if not PDF_ENGINE:
        flash('PDF library not installed. Run: pip install xhtml2pdf', 'danger')
        return redirect(url_for('view_recommendation', rec_id=rec_id))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM ai_recommendations
        WHERE id = %s AND user_id = %s
    """, (rec_id, user_id))
    saved = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()
    cursor.close(); conn.close()

    if not saved:
        flash('Recommendation not found.', 'warning')
        return redirect(url_for('history'))

    ai_data = parse_recommendation(saved)

    html_string = render_template('pdf_template.html',
                                  ai_data=ai_data,
                                  profile=profile_data,
                                  user_name=session['user_name'],
                                  generated_at=saved['created_at'])

    date_str  = saved['created_at'].strftime('%Y-%m-%d')
    safe_name = f"Career_Roadmap_{session['user_name'].replace(' ', '_')}_{date_str}.pdf"

    # PDF generation — try/except is INSIDE this function (correct indentation)
    try:
        pdf_buffer = io.BytesIO()
        pisa.CreatePDF(html_string, dest=pdf_buffer)
        pdf_buffer.seek(0)

        return Response(
            pdf_buffer.read(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{safe_name}"'
            }
        )

    except Exception as e:
        flash(f'PDF generation failed: {str(e)[:100]}', 'danger')
        return redirect(url_for('view_recommendation', rec_id=rec_id))


@app.route('/delete-recommendation/<int:rec_id>', methods=['POST'])
def delete_recommendation(rec_id):
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        DELETE FROM ai_recommendations
        WHERE id = %s AND user_id = %s
    """, (rec_id, session['user_id']))
    conn.commit()

    deleted_count = cursor.rowcount
    cursor.close(); conn.close()

    if deleted_count > 0:
        flash('Recommendation deleted successfully.', 'success')
    else:
        flash('Could not delete. Record not found.', 'warning')

    return redirect(url_for('history'))


# ─────────────────────────────────────────────────────────────────
# DASHBOARD — Updated for Module 4 + Rate Limiting display
# ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn    = get_db_connection()
    cursor  = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile_data = cursor.fetchone()

    cursor.execute("""
        SELECT id, motivational_msg, created_at
        FROM ai_recommendations
        WHERE user_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    last_rec = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS total FROM ai_recommendations
        WHERE user_id = %s
    """, (user_id,))
    count_row  = cursor.fetchone()
    total_recs = count_row['total'] if count_row else 0

    # ── MODULE 5: Calculate cooldown status for dashboard display ──
    # This tells the template whether to show the Get Advice button
    # as active (blue) or disabled (grey with countdown).
    can_generate = True    # default: user is allowed
    cooldown_msg = None    # only set if user is in cooldown

    cursor.execute(
        "SELECT last_recommendation_at FROM users WHERE id = %s", (user_id,)
    )
    rate_row = cursor.fetchone()

    if rate_row and rate_row['last_recommendation_at'] is not None:
        last_time = rate_row['last_recommendation_at']
        now       = datetime.utcnow()
        elapsed   = now - last_time
        cooldown  = timedelta(hours=3)

        if elapsed < cooldown:
            can_generate  = False
            remaining     = cooldown - elapsed
            total_seconds = int(remaining.total_seconds())
            hours_left    = total_seconds // 3600
            minutes_left  = (total_seconds % 3600) // 60
            cooldown_msg  = f"{hours_left}h {minutes_left}m"
    # ── END COOLDOWN CHECK ─────────────────────────────────────────

    cursor.close(); conn.close()

    return render_template('dashboard.html',
                           user_name=session['user_name'],
                           profile=profile_data,
                           last_recommendation=last_rec,
                           total_recs=total_recs,
                           can_generate=can_generate,
                           cooldown_msg=cooldown_msg)
# ─────────────────────────────────────────────────────────────────
# ERROR HANDLERS — Feature 6
# ─────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    """
    Handles 404 errors — page not found.
    Flask automatically calls this whenever a route doesn't exist.
    
    Parameter e: the error object Flask passes in (we don't use it,
                 but the function signature must accept it).
    
    We return TWO things: the rendered template AND the status code 404.
    Why return the status code? Because render_template alone returns 200 (OK).
    Search engines and browsers need the correct 404 code.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    Handles 500 errors — something broke inside Flask.
    This catches unhandled exceptions that crash a route.
    
    Important: We return 500 as the status code, not 200.
    """
    return render_template('500.html'), 500


# ── Run ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)

