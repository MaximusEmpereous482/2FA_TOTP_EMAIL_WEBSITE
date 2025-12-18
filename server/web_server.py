from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from client.client import ChatClient
import os
import time

# --- Инициализация ---
app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
unnormalized_path = os.path.join(BASE_DIR, '..', 'client', 'qr')
# Используем os.path.abspath для полной нормализации пути.
# Это гарантирует, что '..' будет корректно разрешено, и Flask получит чистый абсолютный путь.
QR_FOLDER_PATH = os.path.abspath(unnormalized_path)
print(f"DEBUG READ PATH: {QR_FOLDER_PATH}")
chat_client = ChatClient(port=8000, host='127.0.0.1')


#Проверка аутентификации
@app.before_request
def check_auth():
    if request.endpoint == 'chat' and 'token' not in session:
        return redirect(url_for('auth'))


#Страницы

@app.route('/')
@app.route('/auth')
def auth():
    """Главная страница: Вход/Регистрация"""
    if 'token' in session and 'username' in session:
        return redirect(url_for('chat'))
    return render_template('auth.html')


@app.route('/chat')
def chat():
    """Страница чата"""
    username = session.get('username')
    return render_template('chat.html', username=username)


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('username', None)
    session.pop('token', None)
    return redirect(url_for('auth'))


# НОВЫЙ РОУТ ДЛЯ QR-КОДА
@app.route('/qr_code/<filename>')
def qr_code_file(filename):
    time.sleep(0.5)
    return send_from_directory(QR_FOLDER_PATH, filename)


# API Эндпоинты (Взаимодействие с gRPC)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    login = data.get('login')
    password = data.get('password')

    if not login or not password:
         return jsonify({'error': 'Логин и пароль не могут быть пустыми.'}), 400

    try:
        qr_url = chat_client.register(login, password)

        if qr_url and qr_url.startswith('/qr_code/'):
            # Успешный ответ, включающий URL для клиента
            return jsonify({
                'message': f'Пользователь "{login}" зарегистрирован. Отсканируйте код.',
                'qr_url': qr_url  # Передаем URL в JS
            })
        else:
            # Ошибка, возвращенная из client.py (например, логин занят, ошибка gRPC)
            return jsonify({'error': 'Ошибка регистрации или инициализации 2ФА. Проверьте логи сервера.'}), 400

    except Exception as e:
        # Критическая ошибка сервера (например, gRPC канал недоступен)
        print(f"Критическая ошибка при регистрации: {e}")
        return jsonify({'error': f'Критическая ошибка сервера: {e}'}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    login = data.get('login')
    password = data.get('password')

    token = chat_client.auth(login, password)

    if token:
        return jsonify({
            'success': True,
            'login': login,
            'message': 'Авторизация успешна. Требуется OTP.'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Неверный логин или пароль.'
        }), 401


@app.route('/api/send_otp', methods=['POST'])
def api_send_otp():
    data = request.json
    login = data.get('login')

    success = chat_client.send_email_otp(login)

    if success:
        return jsonify({'success': True, 'message': 'Код отправлен на почту Mailhog.'})
    else:
        return jsonify({'success': False, 'error': 'Ошибка отправки Email OTP. Проверьте Mailhog.'}), 400


@app.route('/api/check_otp', methods=['POST'])
def api_check_otp():
    data = request.json
    login = data.get('login')
    otp_code = data.get('otp')

    is_valid = chat_client.check_otp(login, otp_code)

    if is_valid:
        session['username'] = login
        session['token'] = 'dummy_token'
        return jsonify({'success': True, 'message': 'OTP верный. Вход разрешен.'})
    else:
        return jsonify({'success': False, 'error': 'Неверный или истекший OTP код.'}), 401


@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    data = request.json
    text = data.get('text')
    username = session.get('username')

    if not username:
        return jsonify({'success': False, 'error': 'Не авторизован.'}), 401

    try:
        chat_client.send_message(username, text, time.time())
        return jsonify({'success': True})
    except Exception:
        return jsonify({'success': False, 'error': 'Ошибка отправки сообщения.'}), 500


if __name__ == '__main__':
    if not os.path.exists('../client/qr'):
        os.makedirs('../client/qr')

    print("Запуск Flask сервера. Доступно на http://127.0.0.1:5000")
    app.run(debug=True)