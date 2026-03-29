let currentTask = null;
let tasksData = [];

// 1. Загрузка данных
async function loadTasks() {
    try {
        const response = await fetch('/static/courses.json');
        tasksData = await response.json();
        renderTaskList();
    } catch (err) {
        console.error("Ошибка загрузки JSON:", err);
    }
}

// 2. Отрисовка списка слева
function renderTaskList() {
    const list = document.getElementById('task-list');
    list.innerHTML = '';
    tasksData.forEach((task, index) => {
        const item = document.createElement('div');
        item.className = `task-item ${currentTask?.id === task.id ? 'active' : ''}`;
        item.innerHTML = `<div class="status-icon"></div> ${index + 1}. ${task.title}`;
        item.onclick = () => selectTask(task);
        list.appendChild(item);
    });
}

// 3. Выбор задачи
function selectTask(task) {
    currentTask = task;
    renderTaskList();
    showTheory();
}

// 4. Режим теории
function showTheory() {
    resetUI();
    document.getElementById('lesson-title').innerText = currentTask.title;
    document.getElementById('theory-text').innerHTML = currentTask.theory;
    document.getElementById('theory-section').style.display = 'block';

    const nextBtn = document.getElementById('next-step-btn');
    nextBtn.style.display = 'block';
    nextBtn.innerText = "Я все изучил, к тестам!";
    nextBtn.onclick = showQuiz;
}

// 5. Режим теста (ТВОЯ ЛОГИКА ТУТ)
function showQuiz() {
    resetUI();

    if (!currentTask || !currentTask.quiz) {
        console.error("Данные теста не найдены");
        return;
    }

    const quiz = currentTask.quiz;
    const optionsGrid = document.getElementById('quiz-options');

    // Если вдруг div не найден в HTML
    if (!optionsGrid) {
        console.error("Элемент quiz-options не найден в HTML!");
        return;
    }

    document.getElementById('quiz-section').style.display = 'block';
    document.getElementById('quiz-question').innerText = quiz.question;

    // Очищаем старые кнопки
    optionsGrid.innerHTML = '';

    // Создаем новые кнопки
    quiz.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.innerText = opt;
        btn.onclick = () => handleQuizAnswer(idx, quiz.correct, quiz.explanation, btn);
        optionsGrid.appendChild(btn);
    });
}

function handleQuizAnswer(selectedIndex, correctIndex, explanation, clickedBtn) {
    const allBtns = document.querySelectorAll('.option-btn');
    const feedback = document.getElementById('feedback');

    if (selectedIndex === correctIndex) {
        // ПРАВИЛЬНО
        allBtns.forEach(b => b.style.pointerEvents = 'none'); // Блокируем кнопки
        clickedBtn.style.backgroundColor = '#10b981'; // Зеленый
        clickedBtn.style.color = '#000';

        feedback.innerHTML = `<div class="info-card" style="border-color: #10b981; margin-top: 20px;">
            <b style="color: #10b981;">Правильно.</b> ${explanation}
        </div>`;

        const nextBtn = document.getElementById('next-step-btn');
        nextBtn.style.display = 'block';
        nextBtn.innerText = "Перейти к практике";
        nextBtn.onclick = showPractice;
    } else {
        // НЕПРАВИЛЬНО
        clickedBtn.style.backgroundColor = '#ef4444'; // Красный
        feedback.innerHTML = `<p style="color: #ef4444; margin-top: 10px;">Неверно, попробуй другой вариант.</p>`;
        setTimeout(() => {
            clickedBtn.style.backgroundColor = '';
            feedback.innerHTML = '';
        }, 1000);
    }
}

// 6. Режим практики
function showPractice() {
    resetUI();
    const practice = currentTask.practice;
    document.getElementById('practice-section').style.display = 'block';
    document.getElementById('practice-task').innerText = practice.task;
    document.getElementById('practice-hint').innerText = practice.hint;
    document.getElementById('check-code-btn').style.display = 'block';
}

// 7. Проверка кода
function checkCode() {
    const code = document.getElementById('editor').value.trim();
    const feedback = document.getElementById('feedback');

    if (code === currentTask.practice.expected) {
        feedback.innerHTML = `<p style="color: #10b981; font-weight: 700; margin-top: 10px;">Задание выполнено верно!</p>`;
    } else {
        feedback.innerHTML = `<p style="color: #ef4444; margin-top: 10px;">Результат не совпадает. Проверь код еще раз.</p>`;
    }
}

// Сброс интерфейса перед сменой этапа
function resetUI() {
    // Скрываем все блоки
    document.getElementById('theory-section').style.display = 'none';
    document.getElementById('quiz-section').style.display = 'none';
    document.getElementById('practice-section').style.display = 'none';

    // Скрываем кнопки управления
    document.getElementById('next-step-btn').style.display = 'none';
    const checkBtn = document.getElementById('check-code-btn');
    if (checkBtn) checkBtn.style.display = 'none';

    // Очищаем зону ответа
    const feedback = document.getElementById('feedback');
    if (feedback) feedback.innerHTML = '';
}

window.onload = loadTasks;