/* ─────────────────────────────────────────────────────────────
   EduGenie front-end logic — wish box only
───────────────────────────────────────────────────────────── */

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

async function getJSON(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

/* ── Wish box accordion: open one, close the rest ───────────── */
function toggleWish(id) {
  document.querySelectorAll(".wish-option").forEach((opt) => {
    if (opt.id === id) {
      opt.classList.toggle("open");
    } else {
      opt.classList.remove("open");
    }
  });
}

function buildQuizUI(resultEl, quizData) {
  const cleanQuestions = (quizData || []).filter((q) => !q.error);
  const state = {
    questions: cleanQuestions,
    userAnswers: Array(cleanQuestions.length).fill(null),
    revealed: false,
  };

  resultEl.quizState = state;
  resultEl.innerHTML = `
    <div class="w-quiz-list">
      ${cleanQuestions.map((q, i) => {
        const optionsHtml = (q.options || []).map((opt, idx) => {
          const letter = String.fromCharCode(65 + idx);
          return `<button type="button" class="w-quiz-choice" data-question-index="${i}" data-option-index="${idx}" data-letter="${letter}">${letter}. ${opt}</button>`;
        }).join("");

        return `<div class="w-quiz-q"><strong>Q${i + 1}. ${q.question}</strong><div class="w-quiz-options">${optionsHtml}</div></div>`;
      }).join("")}
    </div>
    <div class="w-quiz-footer">
      <div class="w-quiz-hint">Select one answer for each question. The correct answers will appear after you answer all questions.</div>
      <button type="button" class="w-quiz-submit" disabled>Answer all questions to reveal answers</button>
    </div>
  `;

  resultEl.querySelectorAll(".w-quiz-choice").forEach((btn) => {
    btn.addEventListener("click", () => handleQuizChoiceClick(resultEl, btn));
  });

  updateQuizUI(resultEl);
}

function handleQuizChoiceClick(resultEl, btn) {
  const state = resultEl.quizState;
  if (!state) return;

  const questionIndex = Number(btn.dataset.questionIndex);
  const optionIndex = Number(btn.dataset.optionIndex);
  state.userAnswers[questionIndex] = optionIndex;
  updateQuizUI(resultEl);
}

function updateQuizUI(resultEl) {
  const state = resultEl.quizState;
  if (!state) return;

  const allAnswered = state.userAnswers.every((answer) => answer !== null);
  const submitBtn = resultEl.querySelector(".w-quiz-submit");

  resultEl.querySelectorAll(".w-quiz-choice").forEach((btn) => {
    const questionIndex = Number(btn.dataset.questionIndex);
    const optionIndex = Number(btn.dataset.optionIndex);
    const isSelected = state.userAnswers[questionIndex] === optionIndex;
    btn.classList.toggle("selected", isSelected);

    if (!state.revealed) {
      btn.classList.remove("correct", "wrong");
    }
  });

  if (submitBtn) {
    submitBtn.disabled = !allAnswered || state.revealed;
    submitBtn.textContent = state.revealed
      ? "Answers revealed"
      : allAnswered
        ? "Reveal answers"
        : "Answer all questions to reveal answers";
  }

  if (allAnswered && !state.revealed) {
    revealQuizAnswers(resultEl);
  }
}

function revealQuizAnswers(resultEl) {
  const state = resultEl.quizState;
  if (!state || state.revealed) return;

  state.revealed = true;

  resultEl.querySelectorAll(".w-quiz-q").forEach((questionBlock, questionIndex) => {
    const q = state.questions[questionIndex];
    const correctIndex = (q.correct || "A").charCodeAt(0) - 65;

    questionBlock.querySelectorAll(".w-quiz-choice").forEach((btn) => {
      const optionIndex = Number(btn.dataset.optionIndex);
      const isSelected = state.userAnswers[questionIndex] === optionIndex;
      const isCorrect = optionIndex === correctIndex;

      if (isCorrect) {
        btn.classList.add("correct");
      } else if (isSelected) {
        btn.classList.add("wrong");
      }

      btn.disabled = true;
    });
  });

  const footer = resultEl.querySelector(".w-quiz-footer");
  if (footer) {
    footer.insertAdjacentHTML("beforeend", '<div class="w-quiz-summary">Answers revealed. Review the highlighted correct choice for each question.</div>');
  }

  updateQuizUI(resultEl);
}

/* ── Wish box submit: calls the real backend endpoint for whichever
   option is open, and renders the result inline inside that option ── */
async function wishSubmit(kind) {
  const btn = event.target;
  const resultEl = document.getElementById(`wish-${kind}-result`);
  const originalLabel = btn.textContent;
  resultEl.classList.remove("error");

  const setBusy = (busy) => {
    btn.disabled = busy;
    btn.textContent = busy ? "Working…" : originalLabel;
  };

  try {
    if (kind === "qa") {
      const q = document.getElementById("wish-qa-input").value.trim();
      if (!q) return;
      setBusy(true);
      const data = await getJSON(`/qa?question=${encodeURIComponent(q)}`);
      resultEl.textContent = data.answer;
    } else if (kind === "explain") {
      const topic = document.getElementById("wish-explain-input").value.trim();
      if (!topic) return;
      setBusy(true);
      const data = await postJSON("/explain", { topic });
      resultEl.textContent = data.explanation;
    } else if (kind === "summarize") {
      const text = document.getElementById("wish-summarize-input").value.trim();
      if (!text) return;
      setBusy(true);
      const data = await postJSON("/summarize", { text });
      resultEl.textContent = data.summary;
    } else if (kind === "quiz") {
      const passage = document.getElementById("wish-quiz-input").value.trim();
      if (!passage) return;
      setBusy(true);
      const data = await postJSON("/quiz", { passage });
      const quizData = data.quiz || [];

      if (quizData.some((q) => q.error)) {
        resultEl.innerHTML = quizData.map((q) => `<div class="error">${q.error || "Unable to create quiz."}</div>`).join("");
      } else {
        buildQuizUI(resultEl, quizData);
      }
    } else if (kind === "learn") {
      const topic = document.getElementById("wish-learn-input").value.trim();
      if (!topic) return;
      setBusy(true);
      const data = await getJSON(`/learn/recommendations?topic=${encodeURIComponent(topic)}`);
      resultEl.textContent = data.recommendations;
    }
  } catch (e) {
    resultEl.classList.add("error");
    resultEl.textContent = e.message;
  } finally {
    setBusy(false);
  }
}
