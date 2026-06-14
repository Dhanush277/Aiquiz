import random
import string
from datetime import datetime, timezone
from database.db import supabase

def generate_quiz_code():
    """Generate a unique 9-character alphanumeric quiz code like QZ8K2X91A"""
    while True:
        code = 'QZ' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        # Check if exists
        res = supabase.table('quizzes').select('id').eq('quiz_code', code).execute()
        if not res.data:
            return code

def create_quiz(host_id, title, description, category, difficulty):
    quiz_code = generate_quiz_code()
    data = {
        "host_id": host_id,
        "title": title,
        "description": description,
        "category": category,
        "difficulty": difficulty,
        "quiz_code": quiz_code
    }
    response = supabase.table('quizzes').insert(data).execute()
    if response.data:
        # Also create a default pending session
        session_data = {
            "quiz_id": response.data[0]['id'],
            "status": "pending"
        }
        supabase.table('quiz_sessions').insert(session_data).execute()
        return response.data[0], None
    return None, "Failed to create quiz"

def add_question(quiz_id, question_text, opt_a, opt_b, opt_c, opt_d, correct, explanation, time_limit):
    data = {
        "quiz_id": quiz_id,
        "question_text": question_text,
        "option_a": opt_a,
        "option_b": opt_b,
        "option_c": opt_c,
        "option_d": opt_d,
        "correct_answer": correct,
        "explanation": explanation,
        "time_limit": time_limit
    }
    res = supabase.table('questions').insert(data).execute()
    return res.data[0] if res.data else None

def get_quiz_by_code(quiz_code):
    res = supabase.table('quizzes').select('*').eq('quiz_code', quiz_code).execute()
    return res.data[0] if res.data else None

def join_quiz_session(quiz_id, user_id):
    # Get active or pending session for the quiz (LATEST)
    res = supabase.table('quiz_sessions').select('*').eq('quiz_id', quiz_id).in_('status', ['pending', 'active', 'paused']).order('created_at', desc=True).limit(1).execute()
    if not res.data:
        return None, "No active session for this quiz"
    session_id = res.data[0]['id']
    
    # Add participant
    try:
        part_data = {
            "session_id": session_id,
            "user_id": user_id
        }
        part_res = supabase.table('participants').insert(part_data).execute()
        
        # Initialize score
        if part_res.data:
            participant_id = part_res.data[0]['id']
            supabase.table('scores').insert({"participant_id": participant_id}).execute()
            return participant_id, session_id
    except Exception as e:
        # Might be a duplicate join
        part_res = supabase.table('participants').select('id').eq('session_id', session_id).eq('user_id', user_id).execute()
        if part_res.data:
            return part_res.data[0]['id'], session_id
        return None, str(e)
    return None, "Failed to join"

def get_session_status(session_id):
    res = supabase.table('quiz_sessions').select('*, quizzes(title)').eq('id', session_id).execute()
    if not res.data:
        return None
    session = res.data[0]
    
    # Count participants
    part_count = supabase.table('participants').select('id', count='exact').eq('session_id', session_id).execute().count
    
    # Total questions
    q_count = supabase.table('questions').select('id', count='exact').eq('quiz_id', session['quiz_id']).execute().count

    time_remaining = 0
    if session['status'] == 'active' and session['current_question_id'] and not session['is_paused']:
        q_res = supabase.table('questions').select('time_limit').eq('id', session['current_question_id']).execute()
        if q_res.data:
            time_limit = q_res.data[0]['time_limit']
            started_at = datetime.fromisoformat(session['current_question_started_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            elapsed = (now - started_at).total_seconds()
            time_remaining = max(0, int(time_limit - elapsed))

    return {
        "status": session['status'],
        "current_question_index": session['current_question_index'],
        "current_question_id": session['current_question_id'],
        "time_remaining": time_remaining,
        "participant_count": part_count,
        "total_questions": q_count,
        "is_paused": session['is_paused'],
        "title": session['quizzes']['title']
    }

def update_session_state(session_id, status, q_index=None, q_id=None, is_paused=False):
    data = {"status": status, "is_paused": is_paused}
    if q_index is not None:
        data["current_question_index"] = q_index
    if q_id is not None:
        data["current_question_id"] = q_id
        if q_id:
            data["current_question_started_at"] = datetime.now(timezone.utc).isoformat()
    
    res = supabase.table('quiz_sessions').update(data).eq('id', session_id).execute()
    return res.data[0] if res.data else None

def get_question_details(question_id, for_host=False):
    res = supabase.table('questions').select('*').eq('id', question_id).execute()
    if not res.data:
        return None
    q = res.data[0]
    if not for_host:
        q.pop('correct_answer', None)
        q.pop('explanation', None)
    return q

def submit_answer(participant_id, question_id, selected_answer):
    # Validate session and time
    part_res = supabase.table('participants').select('session_id').eq('id', participant_id).execute()
    if not part_res.data:
        return {"error": "Invalid participant"}
    
    session_id = part_res.data[0]['session_id']
    session_res = supabase.table('quiz_sessions').select('*').eq('id', session_id).execute()
    session = session_res.data[0]
    
    if session['status'] != 'active' or session['is_paused']:
        return {"error": "Quiz is not active"}
    if str(session['current_question_id']) != str(question_id):
        return {"error": "Not the current question"}
        
    q_res = supabase.table('questions').select('correct_answer', 'time_limit').eq('id', question_id).execute()
    q = q_res.data[0]
    
    started_at = datetime.fromisoformat(session['current_question_started_at'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    elapsed = (now - started_at).total_seconds()
    
    if elapsed > q['time_limit']:
        return {"error": "Time limit exceeded"}
        
    is_correct = (selected_answer == q['correct_answer'])
    points = 0
    if is_correct:
        points = 10
        if elapsed <= (0.3 * q['time_limit']):
            points += 2 # Speed bonus
            
    try:
        ans_data = {
            "participant_id": participant_id,
            "question_id": question_id,
            "selected_answer": selected_answer,
            "response_time": round(elapsed, 2),
            "is_correct": is_correct,
            "points": points
        }
        res = supabase.table('answers').insert(ans_data).execute()
        
        # Update score
        update_score(participant_id)
        
        return {"success": True, "points": points, "is_correct": is_correct}
    except Exception as e:
        return {"error": "Answer already submitted or other error"}

def update_score(participant_id):
    ans_res = supabase.table('answers').select('*').eq('participant_id', participant_id).execute()
    answers = ans_res.data
    
    if not answers:
        return
        
    total_points = sum(a['points'] for a in answers)
    correct_count = sum(1 for a in answers if a['is_correct'])
    total_attempted = len(answers)
    accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
    avg_time = sum(a['response_time'] for a in answers) / total_attempted if total_attempted > 0 else 0
    
    supabase.table('scores').update({
        "score": total_points,
        "accuracy": round(accuracy, 2),
        "average_response_time": round(avg_time, 2)
    }).eq('participant_id', participant_id).execute()

def get_leaderboard(session_id):
    part_res = supabase.table('participants').select('id, user_id, users(fullname)').eq('session_id', session_id).execute()
    participants = {p['id']: p['users']['fullname'] for p in part_res.data}
    
    if not participants:
        return []
        
    p_ids = list(participants.keys())
    # Instead of in_ directly because of potential limits, just get all scores and filter
    score_res = supabase.table('scores').select('*').execute()
    scores = [s for s in score_res.data if s['participant_id'] in p_ids]
    
    # Sort by score desc, then avg_time asc
    scores.sort(key=lambda x: (-x['score'], x['average_response_time']))
    
    leaderboard = []
    for idx, s in enumerate(scores):
        # Update rank
        rank = idx + 1
        supabase.table('scores').update({"rank": rank}).eq('id', s['id']).execute()
        
        leaderboard.append({
            "rank": rank,
            "fullname": participants[s['participant_id']],
            "score": s['score'],
            "accuracy": s['accuracy'],
            "average_response_time": s['average_response_time']
        })
    return leaderboard
