// participant.js - Participant polling and live quiz interaction

let currentQuestionId = null;
let timerInterval = null;
let isAnswerLocked = false;
let sessionEnded = false;

function startParticipantPolling(sessionId, participantId) {
    pollStatus(sessionId, participantId);
    setInterval(() => {
        if (!sessionEnded) {
            pollStatus(sessionId, participantId);
        }
    }, 2000);
}

function pollStatus(sessionId, participantId) {
    fetch(`/api/get_session_status/${sessionId}`, { cache: 'no-store' })
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            
            if (data.status === 'pending') {
                showWaitingScreen();
            } else if (data.status === 'paused') {
                showPausedScreen();
            } else if (data.status === 'ended') {
                sessionEnded = true;
                completeQuizAndRedirect(participantId, sessionId);
            } else if (data.status === 'active') {
                // If question changed, fetch new question
                if (data.current_question_id && data.current_question_id !== currentQuestionId) {
                    currentQuestionId = data.current_question_id;
                    isAnswerLocked = false;
                    fetchQuestionDetails(currentQuestionId, data.current_question_index + 1, data.total_questions, data.time_remaining);
                } else if (!isAnswerLocked) {
                    // Just update timer
                    updateTimerUI(data.time_remaining);
                }
            }
        });
}

function fetchQuestionDetails(questionId, qNum, totalQ, timeRemaining) {
    fetch(`/api/get_question_details/${questionId}`, { cache: 'no-store' })
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            renderQuestion(data, qNum, totalQ, timeRemaining);
        });
}

function renderQuestion(qData, qNum, totalQ, timeRemaining) {
    document.getElementById('quiz-container').classList.remove('d-none');
    document.getElementById('waiting-screen').classList.add('d-none');
    
    document.getElementById('progress-text').innerText = `Question ${qNum} of ${totalQ}`;
    document.getElementById('progress-bar').style.width = `${(qNum / totalQ) * 100}%`;
    
    document.getElementById('question-text').innerText = qData.question_text;
    
    const optionsHtml = `
        <div class="row g-3 mt-3">
            <div class="col-md-6"><div class="quiz-option" onclick="selectOption('A', this)">A. ${qData.option_a}</div></div>
            <div class="col-md-6"><div class="quiz-option" onclick="selectOption('B', this)">B. ${qData.option_b}</div></div>
            <div class="col-md-6"><div class="quiz-option" onclick="selectOption('C', this)">C. ${qData.option_c}</div></div>
            <div class="col-md-6"><div class="quiz-option" onclick="selectOption('D', this)">D. ${qData.option_d}</div></div>
        </div>
    `;
    document.getElementById('options-container').innerHTML = optionsHtml;
    
    startLocalTimer(timeRemaining);
}

function selectOption(ans, el) {
    if (isAnswerLocked) return;
    
    const participantId = document.body.dataset.participantId;
    
    // Highlight
    document.querySelectorAll('.quiz-option').forEach(opt => opt.classList.remove('selected'));
    el.classList.add('selected');
    
    // Lock all
    isAnswerLocked = true;
    document.querySelectorAll('.quiz-option').forEach(opt => opt.classList.add('locked'));
    
    // Submit
    fetch('/api/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            participant_id: participantId,
            question_id: currentQuestionId,
            selected_answer: ans
        })
    }).then(res => res.json())
      .then(data => {
          if (data.success) {
              if (data.points > 0) {
                  el.style.borderColor = "var(--success)";
                  el.style.background = "rgba(16, 185, 129, 0.2)";
              } else {
                  el.style.borderColor = "var(--danger)";
                  el.style.background = "rgba(239, 68, 68, 0.2)";
              }
          } else {
              // Unlock so they know it failed, or show error
              el.style.borderColor = "var(--warning)";
              el.style.background = "rgba(245, 158, 11, 0.2)";
              const pText = document.getElementById('progress-text');
              if (pText) pText.innerText = data.error || "Failed to submit answer";
          }
      }).catch(err => {
          console.error(err);
      });
}

function startLocalTimer(seconds) {
    clearInterval(timerInterval);
    let time = seconds;
    updateTimerUI(time);
    
    timerInterval = setInterval(() => {
        time--;
        if (time <= 0) {
            clearInterval(timerInterval);
            if (!isAnswerLocked) {
                isAnswerLocked = true;
                document.querySelectorAll('.quiz-option').forEach(opt => opt.classList.add('locked'));
            }
            const pText = document.getElementById('progress-text');
            if (pText && !pText.innerText.includes("Failed")) {
                pText.innerText = "Time's Up! Waiting for Host...";
                pText.classList.add("text-warning");
            }
        }
        updateTimerUI(time);
    }, 1000);
}

function updateTimerUI(seconds) {
    if (seconds < 0) seconds = 0;
    const timerText = document.getElementById('timer-text');
    if (timerText) timerText.innerText = seconds;
}

function showWaitingScreen() {
    document.getElementById('quiz-container').classList.add('d-none');
    document.getElementById('waiting-screen').classList.remove('d-none');
    document.getElementById('waiting-msg').innerText = "Waiting for Host to start...";
}

function showPausedScreen() {
    document.getElementById('quiz-container').classList.add('d-none');
    document.getElementById('waiting-screen').classList.remove('d-none');
    document.getElementById('waiting-msg').innerText = "Quiz Paused by Host";
}

function completeQuizAndRedirect(participantId, sessionId) {
    document.getElementById('quiz-container').classList.add('d-none');
    document.getElementById('waiting-screen').classList.remove('d-none');
    document.getElementById('waiting-msg').innerText = "Generating AI Report & ML Predictions...";
    
    fetch('/api/complete_quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_id: participantId })
    }).then(() => {
        window.location.href = `/result/${sessionId}/${participantId}`;
    });
}
