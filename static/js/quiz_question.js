/* static/js/quiz_question.js */
(function () {
    'use strict';

    // ── Trạng thái hiện tại ──────────────────────────────────────────────────
    let state = Object.assign({}, QUIZ_STATE);
    // answered = người dùng đã bấm chọn câu này trong phiên hiện tại
    let answered = false;
    // pendingChoiceId = choice vừa click nhưng AJAX chưa về
    let pendingChoiceId = null;
    // navigating = đang tải câu tiếp, chặn click liên tiếp
    let navigating = false;

    // ── DOM references ───────────────────────────────────────────────────────
    const progressBar   = document.getElementById('progress-bar');
    const progressLabel = document.getElementById('progress-label');
    const questionText  = document.getElementById('question-text');
    const choicesCont   = document.getElementById('choices-container');
    const explBox       = document.getElementById('explanation-box');
    const prevBtn       = document.getElementById('prev-btn');
    const nextBtn       = document.getElementById('next-btn');
    const submitBtn     = document.getElementById('submit-btn');
    const questionCard  = document.getElementById('question-card');

    // ── Helpers ──────────────────────────────────────────────────────────────
    const LETTERS = ['A', 'B', 'C', 'D'];

    function getChoiceEls() {
        return Array.from(choicesCont.querySelectorAll('.choice-item'));
    }

    function lockChoices() {
        getChoiceEls().forEach(el => el.style.pointerEvents = 'none');
    }

    function unlockChoices() {
        getChoiceEls().forEach(el => el.style.pointerEvents = '');
    }

    function setChoiceStyle(el, type) {
        el.style.transition = 'background-color 0.2s, border-color 0.2s';
        if (type === 'correct') {
            el.style.backgroundColor = '#d1e7dd';
            el.style.borderColor     = '#198754';
        } else if (type === 'wrong') {
            el.style.backgroundColor = '#f8d7da';
            el.style.borderColor     = '#dc3545';
        } else if (type === 'prev') {
            el.style.backgroundColor = '#fff3cd';
            el.style.borderColor     = '#D69D26';
        } else if (type === 'loading') {
            el.style.backgroundColor = '#e2e8f0';
            el.style.borderColor     = '#94a3b8';
        } else {
            el.style.backgroundColor = '';
            el.style.borderColor     = '';
        }
    }

    function showExplanation(isCorrect, explanation, correctText) {
        explBox.className = 'alert mt-3 mb-0 ' + (isCorrect ? 'alert-success' : 'alert-danger');
        let html = '<strong>' + (isCorrect ? '✓ Đúng!' : '✗ Sai!') + '</strong>';
        if (!isCorrect && correctText) {
            html += ' &nbsp;|&nbsp; <strong>Đáp án đúng:</strong> ' + escHtml(correctText);
        }
        html += '<hr class="my-2"><span>' + escHtml(explanation || 'Không có giải thích.') + '</span>';
        explBox.innerHTML = html;
        explBox.style.display = 'block';
    }

    function escHtml(str) {
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function updateProgress(index, total) {
        const pct = Math.round((index + 1) / total * 100);
        progressBar.style.width = pct + '%';
        progressLabel.textContent = (index + 1) + ' / ' + total;
    }

    function updateNextBtn(isLast) {
        if (isLast) {
            nextBtn.innerHTML = '<i class="bi bi-check2-all me-1"></i>Kết thúc';
        } else {
            nextBtn.innerHTML = 'Câu tiếp theo <i class="bi bi-chevron-right"></i>';
        }
    }

    // ── Khởi tạo câu đã trả lời trước ──────────────────────────────────────
    if (state.selectedChoiceId) {
        const prevEl = document.getElementById('choice-' + state.selectedChoiceId);
        if (prevEl) setChoiceStyle(prevEl, 'prev');
        lockChoices();
        answered = true;
    }

    // ── Xử lý click chọn đáp án ─────────────────────────────────────────────
    choicesCont.addEventListener('click', function (e) {
        const el = e.target.closest('.choice-item');
        if (!el || answered || navigating) return;

        answered = true;
        pendingChoiceId = el.dataset.choiceId;

        // 1. Phản hồi ngay lập tức – không chờ server
        lockChoices();
        setChoiceStyle(el, 'loading');
        el.querySelector('.choice-letter').textContent = '…';

        // 2. Gửi AJAX lên server lưu session + lấy kết quả
        fetch(state.checkAnswerUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': state.csrfToken,
            },
            body: 'choice_id=' + pendingChoiceId + '&quiz_id=' + state.quizId,
        })
        .then(r => r.json())
        .then(data => {
            // Khôi phục chữ cái
            const idx = getChoiceEls().indexOf(el);
            el.querySelector('.choice-letter').textContent = LETTERS[idx] || '?';

            // Tô màu kết quả
            setChoiceStyle(el, data.is_correct ? 'correct' : 'wrong');
            showExplanation(data.is_correct, data.explanation, data.correct_answer_text);
        })
        .catch(() => {
            // Nếu lỗi mạng vẫn cho phép chuyển câu
            const idx = getChoiceEls().indexOf(el);
            el.querySelector('.choice-letter').textContent = LETTERS[idx] || '?';
            setChoiceStyle(el, 'prev');
        });
    });

    // ── Lưu đáp án đang chọn rồi chuyển câu ────────────────────────────────
    function saveAndNavigate(targetIndex) {
        if (navigating) return;

        // Nếu đã answered và đã có pendingChoiceId thì AJAX đã gửi rồi, chỉ cần navigate
        // Nếu chưa answered, chuyển thẳng không cần gửi gì
        navigating = true;
        navigate(targetIndex);
    }

    // ── Chuyển câu bằng AJAX (không reload trang) ────────────────────────────
    function navigate(targetIndex) {
        const url = state.questionJsonUrl.replace('{index}', targetIndex);

        // Hiệu ứng mờ đi
        questionCard.style.opacity = '0.4';
        questionCard.style.transition = 'opacity 0.15s';

        fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
        .then(r => r.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
                return;
            }
            renderQuestion(data);

            // Cập nhật URL không reload
            const pageUrl = state.questionPageUrl.replace('{index}', data.index);
            window.history.pushState({index: data.index}, '', pageUrl);
        })
        .catch(() => {
            // Fallback: reload bình thường nếu lỗi mạng
            const pageUrl = state.questionPageUrl.replace('{index}', targetIndex);
            window.location.href = pageUrl;
        });
    }

    // ── Render dữ liệu câu mới lên DOM ──────────────────────────────────────
    function renderQuestion(data) {
        // Cập nhật state
        state.currentIndex    = data.index;
        state.total           = data.total;
        state.isLast          = data.is_last;
        state.questionId      = data.question.id;
        state.selectedChoiceId = data.selected_choice_id;

        // Nội dung câu hỏi
        questionText.textContent = data.question.text;

        // Render choices
        choicesCont.innerHTML = data.question.choices.map((c, i) =>
            '<div class="choice-item d-flex align-items-start gap-3 p-3 mb-2 rounded border" ' +
                 'data-choice-id="' + c.id + '" id="choice-' + c.id + '">' +
                '<span class="choice-letter badge rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" ' +
                      'style="width:28px;height:28px;min-width:28px;background-color:#D69D26;color:#fff;font-weight:bold;">' +
                    LETTERS[i] +
                '</span>' +
                '<span class="choice-text">' + escHtml(c.text) + '</span>' +
            '</div>'
        ).join('');

        // Reset trạng thái
        explBox.style.display = 'none';
        explBox.innerHTML = '';
        answered  = false;
        navigating = false;
        pendingChoiceId = null;

        // Nếu câu đã được trả lời trước đó
        if (data.selected_choice_id) {
            const prevEl = document.getElementById('choice-' + data.selected_choice_id);
            if (prevEl) setChoiceStyle(prevEl, 'prev');
            lockChoices();
            answered = true;
        } else {
            unlockChoices();
        }

        // Cập nhật progress bar
        updateProgress(data.index, data.total);

        // Cập nhật nút Trước
        prevBtn.disabled = (data.index === 0);

        // Cập nhật nút Tiếp/Kết thúc
        updateNextBtn(data.is_last);

        // Hiệu ứng hiện ra
        questionCard.style.opacity = '1';

        // Cuộn lên đầu câu hỏi
        questionCard.scrollIntoView({behavior: 'smooth', block: 'start'});
    }

    // ── Nút Câu trước ────────────────────────────────────────────────────────
    prevBtn.addEventListener('click', function () {
        if (state.currentIndex > 0) saveAndNavigate(state.currentIndex - 1);
    });

    // ── Nút Câu tiếp / Kết thúc ──────────────────────────────────────────────
    nextBtn.addEventListener('click', function () {
        if (state.isLast) {
            window.location.href = state.reviewUrl;
        } else {
            saveAndNavigate(state.currentIndex + 1);
        }
    });

    // ── Nút Nộp bài ──────────────────────────────────────────────────────────
    submitBtn.addEventListener('click', function () {
        window.location.href = state.resultUrl;
    });

    // ── Trình duyệt Back/Forward ─────────────────────────────────────────────
    window.addEventListener('popstate', function (e) {
        if (e.state && typeof e.state.index === 'number') {
            navigating = false;
            navigate(e.state.index);
        }
    });

})();
