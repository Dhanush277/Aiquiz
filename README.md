# AI-Powered Live Online Quiz Application

A complete, production-ready, industry-standard, submission-ready, and interview-ready AI-Powered Live Online Quiz platform. Built with Python Flask, Supabase (PostgreSQL), Scikit-Learn (Logistic Regression), and Gemini/OpenAI GenAI.

## Overview
This platform allows Hosts to create real-time multiplayer quizzes while Participants join via a unique code. The application uses a robust AJAX polling system for real-time synchronization, server-side timer validation to prevent cheating, and Machine Learning to categorize participant performance. GenAI is leveraged to generate a personalized study report card upon completion.

## Features
- **Live Quizzes:** Real-time polling, Host controls (Start, Pause, Resume, Next, End).
- **Machine Learning Integration:** Logistic Regression categorizes performance into High, Average, or Low based on score, accuracy, and average response time.
- **Generative AI Feedback:** Google Gemini (with OpenAI fallback) generates personalized study tips.
- **Security:** Complete backend timer validation, rate limiting, and password hashing using Werkzeug.
- **Beautiful UI:** Custom CSS with Glassmorphism, Bootstrap 5, and Chart.js analytics.

## Setup Instructions

### 1. Requirements
- Python 3.9+
- Supabase Account
- Google Gemini API Key / OpenAI API Key

### 2. Environment Configuration
Copy the `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Ensure you have `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `GEMINI_API_KEY` set.

### 3. Database Initialization
1. Log into your Supabase Dashboard.
2. Open the **SQL Editor**.
3. Copy the contents of `database/schema.sql` and run it. This will create all 10 tables and necessary indexes.

### 4. Application Execution
Install dependencies and run:
```bash
pip install -r requirements.txt
python app.py
```
*Note: On first boot, the application will automatically generate a 5000+ record synthetic dataset and train the Logistic Regression model (`model.pkl` will be saved).*

## Troubleshooting
- **No Database Connection:** Double check your `.env` keys. If `supabase` throws an auth error, ensure your Anon key is correct.
- **AI Feedback Missing:** Check the server console. If Gemini rate limits you, ensure the `OPENAI_API_KEY` is provided as a fallback.
- **Rate Limit Exceeded:** The app uses Flask-Limiter. If you get a 429, wait a minute before trying to log in/register again.
