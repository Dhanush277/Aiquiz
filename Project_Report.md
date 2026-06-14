# Project Report: AI-Powered Live Online Quiz Application

## Abstract
This project report outlines the architecture, design, and implementation of a next-generation AI-Powered Live Online Quiz Application. By combining a real-time web framework (Flask) with Machine Learning (Scikit-Learn) and Generative AI (Gemini/OpenAI), the system provides an engaging, cheat-proof environment for conducting live assessments with automated, deeply personalized feedback.

## 1. Problem Statement
Traditional online quiz platforms lack robust anti-cheat mechanisms, rely heavily on client-side timers, and offer generic, unhelpful post-quiz feedback. There is a need for a secure, real-time platform that leverages modern AI to actually improve student learning outcomes.

## 2. Objectives
- Build a secure Host-Participant live quiz engine.
- Enforce strict server-side timer validation.
- Implement an ML model to categorize performance profiles.
- Generate personalized study plans using GenAI.
- Create a modern, responsive Glassmorphism UI.

## 3. System Architecture
The application uses a monolithic backend structured into modular components:
- **Backend Core**: Flask handles routing, HTTP requests, and AJAX polling for pseudo-real-time synchronization.
- **Database**: Supabase PostgreSQL serves as the primary data store with Foreign Keys enforcing referential integrity.
- **ML Engine**: A standalone module that trains a Logistic Regression model on startup and exposes a fast inference API.
- **GenAI Engine**: Constructs context-aware prompts combining ML categorizations and numeric scores to generate HTML-formatted feedback.

## 4. Database Schema
The database consists of 10 tables:
1. `users`: Role-based (Host/Participant) with Werkzeug hashed passwords.
2. `quizzes`: Stores quiz metadata and unique join codes.
3. `questions`: Contains correct answers and explanations.
4. `quiz_sessions`: Manages the live state (pending, active, paused, ended).
5. `participants`: Join records linking users to sessions.
6. `answers`: Unique constraint on participant + question prevents duplicate submissions.
7. `scores`: Aggregated participant scores.
8. `predictions`: ML classification output.
9. `ai_feedback`: GenAI generated HTML feedback text.
10. `ai_logs`: Audit trail for LLM prompts and responses.

## 5. API Design
RESTful API endpoints manage the quiz lifecycle:
- `/api/start_quiz`, `/api/pause_quiz`, `/api/next_question`: Host controls.
- `/api/get_session_status`: Polled every 2 seconds by participants to sync UI state.
- `/api/submit_answer`: Server-side calculated response time and scoring logic.
- `/api/complete_quiz`: Triggers ML inference and asynchronous GenAI generation.

## 6. Machine Learning Implementation
A synthetic dataset of 5,000+ records was generated reflecting three profiles: High Performer, Average Performer, and Low Performer. Features include `score`, `accuracy`, `average_response_time`, and `questions_attempted`.
A **Logistic Regression** model (`saga` solver) was trained, achieving high accuracy. The model was serialized via `joblib` alongside a `StandardScaler`.

## 7. Generative AI Implementation
The Gemini API acts as the primary LLM provider. The system constructs a prompt injecting the ML output and exact quiz statistics. If Gemini is unavailable, it gracefully falls back to the OpenAI API (`gpt-3.5-turbo`). Responses are cached in the database to minimize API costs.

## 8. Security Considerations
- **Timer Tampering:** Response time is derived entirely from `current_question_started_at` in the DB.
- **Rate Limiting:** `Flask-Limiter` protects authentication routes.
- **SQL Injection:** The Supabase Python client handles parameterization safely.
- **Data Leaks:** The `/api/get_question_details` endpoint explicitly scrubs `correct_answer` and `explanation` before sending to participants.

## 9. Conclusion
The AI-Powered Live Online Quiz Application successfully integrates traditional web architecture with cutting-edge AI features. It proves that real-time polling combined with server-side validation can create a secure assessment environment, while ML and GenAI turn a simple test into a personalized learning experience.

## 10. Future Scope
- Implementation of WebSockets for lower-latency communication.
- Expansion of the ML module to predict specific knowledge gaps per category.
- Exporting AI reports to PDF.
