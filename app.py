import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    xp = db.Column(db.Integer, default=0)
    # Здесь можно хранить список купленных или доступных языков через запятую
    languages = db.Column(db.String(200), default='python')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def load_courses():
    with open('courses.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_code(text):
    """
    Приводит код к единому виду для честной проверки:
    - Заменяет двойные кавычки на одинарные
    - Убирает лишние пробелы в начале/конце строк
    - Игнорирует пустые строки
    """
    if not text:
        return ""
    # Заменяем " на '
    text = text.replace('"', "'")
    # Чистим каждую строку от лишних пробелов по бокам и убираем пустые строки
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return "\n".join(lines)


# --- МАРШРУТЫ (ROUTES) ---

@app.route('/')
@login_required
def index():
    courses = load_courses()
    user_langs = current_user.languages.split(',')
    # Добавляем временную метку для сброса кэша стилей
    import time
    return render_template('index.html',
                           courses=courses,
                           user_langs=user_langs,
                           cache_v=int(time.time()))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('auth.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Пользователь уже существует')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/check_code', methods=['POST'])
@login_required
def check_code():
    data = request.json
    lang = data.get('lang')
    task_id = int(data.get('id'))
    user_code = data.get('code', '')

    courses = load_courses()
    # Ищем задачу по ID
    task = next((t for t in courses[lang] if t['id'] == task_id), None)

    if not task:
        return jsonify({'success': False, 'error': 'Task not found'})

    # Сравниваем нормализованный код пользователя и эталон
    if normalize_code(user_code) == normalize_code(task['answer']):
        current_user.xp += 15
        db.session.commit()
        return jsonify({'success': True, 'xp': current_user.xp})
    else:
        return jsonify({'success': False})


# --- ЗАПУСК ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем базу данных, если её нет
    app.run(debug=True)