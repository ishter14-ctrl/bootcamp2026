from flask import Flask, render_template_string, request, jsonify
from peewee import *
from datetime import datetime
import os

app = Flask(__name__)

# Настройка базы данных SQLite
db = SqliteDatabase('comments.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField(unique=True)
    created_at = DateTimeField(default=datetime.now)


class Comment(BaseModel):
    author_name = CharField()
    text = TextField()
    parent = ForeignKeyField('self', null=True, backref='replies')
    created_at = DateTimeField(default=datetime.now)
    likes = IntegerField(default=0)

    class Meta:
        table_name = 'comments'


# Инициализация базы данных
db.connect()
db.create_tables([User, Comment], safe=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☁️ Облачные комментарии</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        /* Фоновое изображение на весь экран */
        .background-image {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://avatars.mds.yandex.net/i?id=e35cb8c8f01b81aa8ce90af7f4e040d7_l-5207170-images-thumbs&ref=rim&n=13&w=1280&h=720');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            filter: brightness(0.7);
            z-index: 0;
        }

        .content {
            position: relative;
            z-index: 1;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.2) 100%);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 25px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .header h1 {
            color: white;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1em;
        }

        .user-greeting {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: bold;
        }

        .name-input {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .name-input.active {
            display: flex;
        }

        .name-input-content {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
            backdrop-filter: blur(20px);
            padding: 40px;
            border-radius: 30px;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.5);
            text-align: center;
            max-width: 400px;
            width: 90%;
            border: 2px solid rgba(255, 255, 255, 0.5);
        }

        .name-input-content h2 {
            color: #2d3436;
            margin-bottom: 15px;
            font-size: 1.8em;
        }

        .name-input-content p {
            color: #636e72;
            margin-bottom: 20px;
        }

        .name-input input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #dfe6e9;
            border-radius: 15px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
        }

        .name-input input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
            background: white;
        }

        .name-input button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .name-input button:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }

        .comment-form {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 25px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }

        .comment-form:hover {
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.4);
            transform: translateY(-2px);
        }

        .comment-form h2 {
            color: white;
            margin-bottom: 20px;
            font-size: 1.5em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }

        .form-group {
            position: relative;
            margin-bottom: 20px;
        }

        .comment-form textarea {
            width: 100%;
            padding: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            font-size: 16px;
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }

        .comment-form textarea:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.6);
            box-shadow: 0 0 30px rgba(102, 126, 234, 0.2);
            background: rgba(255, 255, 255, 0.2);
        }

        .comment-form textarea::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 35px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }

        .submit-btn:active {
            transform: translateY(0);
        }

        .submit-btn::before {
            content: "✈️";
            font-size: 1.2em;
        }

        .comments-list {
            margin-top: 30px;
        }

        .comment {
            margin-bottom: 25px;
            animation: slideIn 0.5s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .comment-content {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(15px);
            padding: 25px;
            border-radius: 30px;
            position: relative;
            margin-bottom: 10px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .comment-content:hover {
            transform: translateX(5px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 0.25);
        }

        /* Эффект облака */
        .comment-content::before {
            content: '';
            position: absolute;
            top: -15px;
            left: 20px;
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-bottom: 15px solid rgba(255, 255, 255, 0.15);
        }

        .comment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }

        .comment-author {
            font-weight: 700;
            color: #a8d8ff;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 1.1em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }

        .comment-author::before {
            content: "👤";
        }

        .comment-date {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .comment-date::before {
            content: "🕒";
        }

        .comment-text {
            margin: 15px 0;
            line-height: 1.8;
            color: white;
            font-size: 1.05em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }

        .comment-actions {
            display: flex;
            gap: 15px;
            align-items: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px solid rgba(255, 255, 255, 0.1);
        }

        .like-btn {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            box-shadow: 0 8px 25px rgba(238, 90, 36, 0.3);
        }

        .like-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 12px 35px rgba(238, 90, 36, 0.4);
        }

        .like-btn:active {
            transform: scale(0.95);
        }

        .like-btn.liked {
            animation: likeAnimation 0.6s ease;
        }

        @keyframes likeAnimation {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }

        .reply-btn {
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            box-shadow: 0 8px 25px rgba(0, 206, 201, 0.3);
        }

        .reply-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 12px 35px rgba(0, 206, 201, 0.4);
        }

        .replies {
            margin-left: 50px;
            border-left: 3px solid rgba(255, 255, 255, 0.2);
            padding-left: 30px;
            margin-top: 20px;
        }

        .reply-form {
            display: none;
            margin-top: 15px;
            margin-left: 50px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: slideDown 0.3s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .reply-form.active {
            display: block;
        }

        .reply-form textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            resize: vertical;
            min-height: 80px;
            font-family: inherit;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }

        .reply-form textarea:focus {
            outline: none;
            border-color: rgba(0, 184, 148, 0.6);
            box-shadow: 0 0 20px rgba(0, 184, 148, 0.2);
            background: rgba(255, 255, 255, 0.2);
        }

        .reply-form textarea::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .reply-form .submit-reply-btn {
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 12px;
            cursor: pointer;
            margin-top: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 184, 148, 0.3);
        }

        .reply-form .submit-reply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(0, 184, 148, 0.4);
        }

        @media (max-width: 768px) {
            .content {
                padding: 10px;
            }

            .comment-form, .header {
                padding: 20px;
            }

            .replies {
                margin-left: 20px;
                padding-left: 15px;
            }

            .comment-actions {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="background-image"></div>

    <div class="content">
        <div class="header">
            <h1>☁️ Облачные комментарии</h1>
            <p>Добро пожаловать, <span class="user-greeting" id="currentUser">Гость</span>! Делитесь своими мыслями ✨</p>
        </div>

        <div class="comment-form">
            <h2>💭 Оставить комментарий</h2>
            <div class="form-group">
                <textarea id="commentText" placeholder="Напишите, что вы думаете..."></textarea>
            </div>
            <button class="submit-btn" onclick="addComment()">Отправить комментарий</button>
        </div>

        <div class="comments-list" id="commentsList">
            <!-- Комментарии будут здесь -->
        </div>
    </div>

    <div class="name-input" id="nameModal">
        <div class="name-input-content">
            <h2>🌟 Добро пожаловать!</h2>
            <p>Пожалуйста, представьтесь перед тем как начать общение:</p>
            <input type="text" id="userNameInput" placeholder="Ваше имя" autocomplete="off">
            <button onclick="saveName()">Начать общение 🚀</button>
        </div>
    </div>

    <script>
        let currentUserName = localStorage.getItem('userName') || '';

        // Проверка имени пользователя при загрузке
        window.onload = function() {
            if (!currentUserName) {
                document.getElementById('nameModal').classList.add('active');
                document.getElementById('userNameInput').focus();
            } else {
                document.getElementById('currentUser').textContent = currentUserName;
                loadComments();
            }
        };

        // Сохранение имени пользователя
        function saveName() {
            const name = document.getElementById('userNameInput').value.trim();
            if (name) {
                currentUserName = name;
                localStorage.setItem('userName', name);
                document.getElementById('currentUser').textContent = name;
                document.getElementById('nameModal').classList.remove('active');
                loadComments();
            }
        }

        // Обработка Enter в поле имени
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                if (document.getElementById('nameModal').classList.contains('active')) {
                    saveName();
                }
            }
        });

        // Загрузка комментариев
        function loadComments() {
            fetch('/api/comments')
                .then(response => response.json())
                .then(comments => {
                    displayComments(comments);
                });
        }

        // Отображение комментариев
        function displayComments(comments) {
            const container = document.getElementById('commentsList');
            container.innerHTML = '';

            comments.forEach(comment => {
                if (!comment.parent_id) {
                    container.appendChild(createCommentElement(comment, comments));
                }
            });
        }

        // Создание элемента комментария
        function createCommentElement(comment, allComments) {
            const div = document.createElement('div');
            div.className = 'comment';

            const date = new Date(comment.created_at);
            const formattedDate = date.toLocaleString('ru-RU', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            const replies = allComments.filter(c => c.parent_id === comment.id);
            const isSecondLevel = comment.parent_id !== null;

            // Показываем кнопку "Ответить" только для комментариев первого уровня
            const replyButton = !isSecondLevel ? `
                <button class="reply-btn" onclick="showReplyForm(${comment.id})">
                    💬 Ответить
                </button>
            ` : '';

            // Форма ответа показывается только для комментариев первого уровня
            const replyForm = !isSecondLevel ? `
                <div class="reply-form" id="replyForm-${comment.id}">
                    <textarea id="replyText-${comment.id}" placeholder="Напишите ответ..."></textarea>
                    <button class="submit-reply-btn" onclick="addReply(${comment.id})">✉️ Отправить ответ</button>
                </div>
            ` : '';

            div.innerHTML = `
                <div class="comment-content">
                    <div class="comment-header">
                        <span class="comment-author">${escapeHtml(comment.author_name)}</span>
                        <span class="comment-date">${formattedDate}</span>
                    </div>
                    <div class="comment-text">${escapeHtml(comment.text)}</div>
                    <div class="comment-actions">
                        <button class="like-btn" onclick="likeComment(${comment.id}, this)">
                            ❤️ <span id="likes-${comment.id}">${comment.likes}</span>
                        </button>
                        ${replyButton}
                    </div>
                </div>
                ${replyForm}
                ${replies.length > 0 ? `
                    <div class="replies">
                        ${replies.map(reply => createCommentElement(reply, allComments).outerHTML).join('')}
                    </div>
                ` : ''}
            `;

            return div;
        }

        // Добавление комментария
        function addComment() {
            const textarea = document.getElementById('commentText');
            const text = textarea.value.trim();
            if (!text || !currentUserName) return;

            fetch('/api/comments', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    author_name: currentUserName,
                    text: text,
                    parent_id: null
                })
            })
            .then(response => response.json())
            .then(() => {
                textarea.value = '';
                loadComments();
            });
        }

        // Показать форму ответа
        function showReplyForm(commentId) {
            const form = document.getElementById('replyForm-' + commentId);
            const textarea = document.getElementById('replyText-' + commentId);

            if (form.classList.contains('active')) {
                form.classList.remove('active');
            } else {
                // Закрываем все другие формы
                document.querySelectorAll('.reply-form').forEach(f => f.classList.remove('active'));
                form.classList.add('active');
                textarea.focus();
            }
        }

        // Добавление ответа
        function addReply(parentId) {
            const textarea = document.getElementById('replyText-' + parentId);
            const text = textarea.value.trim();
            if (!text || !currentUserName) return;

            fetch('/api/comments', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    author_name: currentUserName,
                    text: text,
                    parent_id: parentId
                })
            })
            .then(response => response.json())
            .then(() => {
                loadComments();
            });
        }

        // Лайк комментария
        function likeComment(commentId, button) {
            fetch('/api/comments/' + commentId + '/like', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                const likesSpan = document.getElementById('likes-' + commentId);
                if (likesSpan) {
                    likesSpan.textContent = data.likes;
                    // Анимация лайка
                    button.classList.add('liked');
                    setTimeout(() => button.classList.remove('liked'), 600);
                }
            });
        }

        // Защита от XSS
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


# API эндпоинты
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/comments', methods=['GET'])
def get_comments():
    comments = Comment.select().order_by(Comment.created_at.desc())
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'author_name': comment.author_name,
            'text': comment.text,
            'parent_id': comment.parent_id if comment.parent else None,
            'created_at': comment.created_at.isoformat(),
            'likes': comment.likes
        })
    return jsonify(comments_data)


@app.route('/api/comments', methods=['POST'])
def add_comment():
    data = request.json
    author_name = data.get('author_name', '').strip()
    text = data.get('text', '').strip()
    parent_id = data.get('parent_id')

    if not author_name or not text:
        return jsonify({'error': 'Имя и текст обязательны'}), 400

    # Если есть parent_id, проверяем существование родительского комментария
    if parent_id:
        try:
            parent_comment = Comment.get_by_id(parent_id)
        except Comment.DoesNotExist:
            return jsonify({'error': 'Родительский комментарий не найден'}), 404

    comment = Comment.create(
        author_name=author_name,
        text=text,
        parent=parent_id
    )

    return jsonify({
        'id': comment.id,
        'author_name': comment.author_name,
        'text': comment.text,
        'parent_id': comment.parent_id,
        'created_at': comment.created_at.isoformat(),
        'likes': comment.likes
    })


@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    try:
        comment = Comment.get_by_id(comment_id)
        comment.likes += 1
        comment.save()
        return jsonify({'likes': comment.likes, 'message': 'Лайк добавлен'})
    except Comment.DoesNotExist:
        return jsonify({'error': 'Комментарий не найден'}), 404


# Создание папки для статических файлов при необходимости
if not os.path.exists('static'):
    os.makedirs('static')

if __name__ == '__main__':
    app.run(debug=True, port=5000)