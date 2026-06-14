import os
import joblib
import google.generativeai as genai
import openai
from config.settings import Config
from database.db import supabase

# Setup Absolute Paths for Vercel Compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'ml', 'scaler.pkl')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except:
    model = None
    scaler = None

# Initialize APIs
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)

if Config.OPENAI_API_KEY:
    openai.api_key = Config.OPENAI_API_KEY

def generate_and_save_feedback(participant_id, score_data, predicted_category):
    # Construct Prompt
    prompt = f"""
    You are an expert AI Quiz Tutor. Analyze the participant's performance and provide personalized, constructive feedback.
    
    Performance Data:
    - Total Score: {score_data['score']}
    - Accuracy: {score_data['accuracy']}%
    - Average Response Time: {score_data['average_response_time']} seconds per question
    - Machine Learning Classification: {predicted_category}
    
    Provide:
    1. A short, encouraging summary of their performance.
    2. Specific analysis of their accuracy vs speed.
    3. 3 actionable tips for improvement based on their '{predicted_category}' profile.
    
    Format the response nicely in HTML format (using <b>, <ul>, <li>) so it can be directly embedded in the results dashboard. Do not use markdown backticks around the HTML.
    """
    
    response_text = "AI Feedback is currently unavailable."
    
    # Try Gemini First
    if Config.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt)
            response_text = response.text
        except Exception as e:
            print(f"Gemini API failed: {e}. Falling back to OpenAI...")
            response_text = try_openai_fallback(prompt)
    else:
        # Fallback to OpenAI directly if Gemini not configured
        response_text = try_openai_fallback(prompt)
        
    if response_text.startswith("```html"):
        response_text = response_text[7:-3]
        
    # Save Feedback
    try:
        supabase.table('ai_feedback').insert({
            "participant_id": participant_id,
            "feedback_text": response_text
        }).execute()
        
        # Log Prompt
        supabase.table('ai_logs').insert({
            "participant_id": participant_id,
            "prompt": prompt,
            "response": response_text
        }).execute()
    except Exception as e:
        print(f"Error saving AI feedback to DB: {e}")

def try_openai_fallback(prompt):
    if not Config.OPENAI_API_KEY:
        return "Both primary (Gemini) and fallback (OpenAI) APIs are unavailable or not configured. Great effort on the quiz! Keep practicing to improve."
        
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful quiz tutor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI fallback failed: {e}")
        return "AI APIs are currently experiencing high load. You performed like a " + prompt.split('Machine Learning Classification: ')[1].split('\n')[0] + " - keep up the great work!"
