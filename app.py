from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка времени жизни сессии (30 дней), чтобы не выкидывало из аккаунта
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- МОДЕЛЬ ДАННЫХ ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    xp = db.Column(db.Integer, default=0)
    # Храним ID уроков как строку через запятую: "1,2,3"
    completed_lessons = db.Column(db.String(500), default="")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- МАРШРУТЫ АУТЕНТИФИКАЦИИ ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)
        return redirect(url_for('course'))

    return render_template('auth.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('course'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('auth.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- ОСНОВНЫЕ МАРШРУТЫ ---

@app.route('/')
def index():
    # УБРАН принудительный редирект в учебник.
    # Теперь клик по логотипу всегда открывает главную (landing) страницу.
    return render_template('index.html')


@app.route('/course')
@login_required
def course():
    return render_template('course.html', user=current_user)


@app.route('/profile')
@login_required
def profile():
    if current_user.completed_lessons:
        completed_count = len([x for x in current_user.completed_lessons.split(',') if x.strip()])
    else:
        completed_count = 0

    total_lessons = 50
    progress_percent = int((completed_count / total_lessons) * 100)
    if progress_percent > 100:
        progress_percent = 100

    if current_user.xp < 100:
        rank = "Новичок"
    elif current_user.xp < 250:
        rank = "Ученик"
    elif current_user.xp < 400:
        rank = "Программист"
    else:
        rank = "Python-Мастер"

    return render_template('profile.html',
                           user=current_user,
                           completed_count=completed_count,
                           total_lessons=total_lessons,
                           progress_percent=progress_percent,
                           rank=rank)


# --- API ДЛЯ ПРОГРЕССА ---

@app.route('/api/get_progress')
@login_required
def get_progress():
    if current_user.completed_lessons:
        ids = [int(x) for x in current_user.completed_lessons.split(',') if x.strip()]
    else:
        ids = []
    return jsonify({"completed_lessons": ids, "xp": current_user.xp})


@app.route('/api/save_progress', methods=['POST'])
@login_required
def save_progress():
    data = request.get_json()
    lesson_id = str(data.get('lesson_id'))

    user = User.query.get(current_user.id)
    completed_list = [x.strip() for x in user.completed_lessons.split(',') if x.strip()]

    if lesson_id not in completed_list:
        completed_list.append(lesson_id)
        user.completed_lessons = ",".join(completed_list)
        user.xp += 15
        db.session.commit()
        return jsonify({"status": "success", "new_xp": user.xp})

    return jsonify({"status": "already_done"})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)