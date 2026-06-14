from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.auth import create_user, verify_user_login
from backend.quiz_manager import (
    create_quiz, add_question, get_quiz_by_code, join_quiz_session,
    get_session_status, update_session_state, get_question_details,
    submit_answer, get_leaderboard, update_score
)
from database.db import supabase
from functools import wraps

main_bp = Blueprint('main', __name__)

def host_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'host':
            flash('Access denied. Host role required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- PAGES ---

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user, error = create_user(fullname, username, email, password, role)
        if error:
            flash(error, 'danger')
        else:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = verify_user_login(email, password)
        if user:
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'host':
        res = supabase.table('quizzes').select('*').eq('host_id', current_user.id).execute()
        quizzes = res.data if res.data else []
        return render_template('dashboard.html', quizzes=quizzes)
    else:
        return render_template('join_quiz.html')

@main_bp.route('/create_quiz', methods=['GET', 'POST'])
@login_required
@host_required
def route_create_quiz():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty')
        
        quiz, err = create_quiz(current_user.id, title, description, category, difficulty)
        if quiz:
            flash('Quiz created! Now add questions.', 'success')
            return redirect(url_for('main.route_add_question', quiz_id=quiz['id']))
        else:
            flash(err, 'danger')
    return render_template('create_quiz.html')

@main_bp.route('/add_question/<quiz_id>', methods=['GET', 'POST'])
@login_required
@host_required
def route_add_question(quiz_id):
    if request.method == 'POST':
        text = request.form.get('question_text')
        a = request.form.get('option_a')
        b = request.form.get('option_b')
        c = request.form.get('option_c')
        d = request.form.get('option_d')
        correct = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        time_limit = int(request.form.get('time_limit', 30))
        
        q = add_question(quiz_id, text, a, b, c, d, correct, explanation, time_limit)
        if q:
            flash('Question added successfully.', 'success')
        else:
            flash('Failed to add question.', 'danger')
    
    # get questions
    res = supabase.table('questions').select('*').eq('quiz_id', quiz_id).execute()
    questions = res.data if res.data else []
    return render_template('add_question.html', quiz_id=quiz_id, questions=questions)

@main_bp.route('/host_panel/<quiz_id>')
@login_required
@host_required
def host_panel(quiz_id):
    quiz_res = supabase.table('quizzes').select('*').eq('id', quiz_id).execute()
    quiz = quiz_res.data[0] if quiz_res.data else None
    
    # Get the latest session for this quiz
    session_res = supabase.table('quiz_sessions').select('*').eq('quiz_id', quiz_id).order('created_at', desc=True).limit(1).execute()
    session = session_res.data[0] if session_res.data else None
    
    return render_template('host_panel.html', quiz=quiz, session=session)

@main_bp.route('/create_new_session/<quiz_id>', methods=['POST'])
@login_required
@host_required
def create_new_session(quiz_id):
    session_data = {
        "quiz_id": quiz_id,
        "status": "pending"
    }
    res = supabase.table('quiz_sessions').insert(session_data).execute()
    if res.data:
        flash('New session created! Participants can now join.', 'success')
    else:
        flash('Failed to create new session.', 'danger')
    return redirect(url_for('main.host_panel', quiz_id=quiz_id))

@main_bp.route('/join_quiz', methods=['POST'])
@login_required
def route_join_quiz():
    quiz_code = request.form.get('quiz_code')
    quiz = get_quiz_by_code(quiz_code)
    if not quiz:
        flash('Invalid quiz code.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    participant_id, session_id = join_quiz_session(quiz['id'], current_user.id)
    if not participant_id:
        flash(session_id, 'danger') # error message
        return redirect(url_for('main.dashboard'))
        
    return redirect(url_for('main.live_quiz', session_id=session_id, participant_id=participant_id))

@main_bp.route('/live_quiz/<session_id>/<participant_id>')
@login_required
def live_quiz(session_id, participant_id):
    # Security check: verify this participant belongs to current_user
    res = supabase.table('participants').select('user_id').eq('id', participant_id).execute()
    if not res.data or res.data[0]['user_id'] != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    return render_template('live_quiz.html', session_id=session_id, participant_id=participant_id)

@main_bp.route('/result/<session_id>/<participant_id>')
@login_required
def result(session_id, participant_id):
    # Only load results here
    res = supabase.table('scores').select('*').eq('participant_id', participant_id).execute()
    score_data = res.data[0] if res.data else None
    
    # get ml and ai feedback
    pred_res = supabase.table('predictions').select('*').eq('participant_id', participant_id).execute()
    prediction = pred_res.data[0] if pred_res.data else None
    
    ai_res = supabase.table('ai_feedback').select('*').eq('participant_id', participant_id).execute()
    feedback = ai_res.data[0] if ai_res.data else None
    
    return render_template('result.html', score=score_data, prediction=prediction, feedback=feedback)

@main_bp.route('/admin_analytics')
@login_required
@host_required
def admin_analytics():
    # 1. Total Participants
    part_res = supabase.table('participants').select('id', count='exact').execute()
    total_participants = part_res.count if part_res.count else 0
    
    # 2. Avg Platform Score
    score_res = supabase.table('scores').select('accuracy').execute()
    if score_res.data:
        avg_score = sum(s['accuracy'] for s in score_res.data) / len(score_res.data)
    else:
        avg_score = 0
        
    # 3. ML Predictions
    pred_res = supabase.table('predictions').select('predicted_category').execute()
    total_predictions = len(pred_res.data) if pred_res.data else 0
    
    high = sum(1 for p in pred_res.data if p['predicted_category'] == 'High Performer') if pred_res.data else 0
    avg = sum(1 for p in pred_res.data if p['predicted_category'] == 'Average Performer') if pred_res.data else 0
    low = sum(1 for p in pred_res.data if p['predicted_category'] == 'Low Performer') if pred_res.data else 0
    
    # 4. AI Reports
    ai_res = supabase.table('ai_feedback').select('id', count='exact').execute()
    total_ai = ai_res.count if ai_res.count else 0
    
    # 5. Scatter Data
    scatter_data = []
    full_scores = supabase.table('scores').select('average_response_time', 'accuracy').execute()
    if full_scores.data:
        scatter_data = [{"x": s['average_response_time'], "y": s['accuracy']} for s in full_scores.data]
        
    return render_template('admin_analytics.html', 
        total_participants=total_participants,
        avg_score=round(avg_score, 1),
        total_predictions=total_predictions,
        total_ai=total_ai,
        pie_data=[high, avg, low],
        scatter_data=scatter_data
    )

# --- APIs (AJAX Endpoints) ---

@main_bp.route('/api/start_quiz/<session_id>', methods=['POST'])
@login_required
@host_required
def start_quiz(session_id):
    # Fetch first question
    s_res = supabase.table('quiz_sessions').select('quiz_id').eq('id', session_id).execute()
    if not s_res.data:
        return jsonify({"error": "Session not found"}), 404
        
    q_res = supabase.table('questions').select('id').eq('quiz_id', s_res.data[0]['quiz_id']).order('id').limit(1).execute()
    if not q_res.data:
        return jsonify({"error": "No questions found"}), 400
        
    update_session_state(session_id, 'active', q_index=0, q_id=q_res.data[0]['id'], is_paused=False)
    return jsonify({"success": True})

@main_bp.route('/api/pause_quiz/<session_id>', methods=['POST'])
@login_required
@host_required
def pause_quiz(session_id):
    update_session_state(session_id, 'paused', is_paused=True)
    return jsonify({"success": True})

@main_bp.route('/api/resume_quiz/<session_id>', methods=['POST'])
@login_required
@host_required
def resume_quiz(session_id):
    update_session_state(session_id, 'active', is_paused=False)
    return jsonify({"success": True})

@main_bp.route('/api/next_question/<session_id>', methods=['POST'])
@login_required
@host_required
def next_question(session_id):
    # Get current index and next question
    s_res = supabase.table('quiz_sessions').select('*').eq('id', session_id).execute()
    session = s_res.data[0]
    
    idx = session['current_question_index'] + 1
    # order by id to get consistent sequence
    q_res = supabase.table('questions').select('id').eq('quiz_id', session['quiz_id']).order('id').execute()
    
    if idx < len(q_res.data):
        update_session_state(session_id, 'active', q_index=idx, q_id=q_res.data[idx]['id'])
        return jsonify({"success": True})
    else:
        # no more questions
        return jsonify({"error": "No more questions"}), 400

@main_bp.route('/api/end_quiz/<session_id>', methods=['POST'])
@login_required
@host_required
def end_quiz(session_id):
    update_session_state(session_id, 'ended', is_paused=False)
    return jsonify({"success": True})

@main_bp.route('/api/get_session_status/<session_id>', methods=['GET'])
@login_required
def api_get_session_status(session_id):
    status = get_session_status(session_id)
    if not status:
        return jsonify({"error": "Not found"}), 404
    return jsonify(status)

@main_bp.route('/api/get_question_details/<question_id>', methods=['GET'])
@login_required
def api_get_question_details(question_id):
    # Return limited details (no answer/explanation)
    # The host panel might want full details, but we secure this endpoint
    is_host = (current_user.role == 'host')
    q = get_question_details(question_id, for_host=is_host)
    if not q:
        return jsonify({"error": "Not found"}), 404
    return jsonify(q)

@main_bp.route('/api/submit_answer', methods=['POST'])
@login_required
def api_submit_answer():
    data = request.json
    participant_id = data.get('participant_id')
    question_id = data.get('question_id')
    selected_answer = data.get('selected_answer')
    
    res = submit_answer(participant_id, question_id, selected_answer)
    return jsonify(res)

@main_bp.route('/api/leaderboard/<session_id>', methods=['GET'])
@login_required
def api_leaderboard(session_id):
    board = get_leaderboard(session_id)
    return jsonify({"leaderboard": board})

@main_bp.route('/api/complete_quiz', methods=['POST'])
@login_required
def complete_quiz():
    data = request.json
    participant_id = data.get('participant_id')
    
    # Check if we already predicted to avoid duplicate runs
    res = supabase.table('predictions').select('id').eq('participant_id', participant_id).execute()
    if res.data:
        return jsonify({"success": True, "message": "Already processed"})
        
    # Kick off ML inference and AI Gen
    from ml.train_model import predict_performance
    from genai.feedback_generator import generate_and_save_feedback
    
    # Get score
    score_res = supabase.table('scores').select('*').eq('participant_id', participant_id).execute()
    if not score_res.data:
        return jsonify({"error": "Score not found"}), 404
    
    score_data = score_res.data[0]
    
    # Get answers count to pass to ML
    ans_res = supabase.table('answers').select('id', count='exact').eq('participant_id', participant_id).execute()
    questions_attempted = ans_res.count if ans_res.count else 0
    
    predicted_category = predict_performance(
        score_data['score'], 
        score_data['accuracy'], 
        score_data['average_response_time'], 
        questions_attempted
    )
    
    if predicted_category:
        supabase.table('predictions').insert({
            "participant_id": participant_id,
            "predicted_category": predicted_category
        }).execute()
        
        # Trigger GenAI
        generate_and_save_feedback(participant_id, score_data, predicted_category)
        
    return jsonify({"success": True})
