from flask import Flask, request, render_template_string, redirect, url_for, make_response, abort
import redis
import pymysql
import time
from functools import wraps
from redis.sentinel import Sentinel  # Sentinel을 위한 모듈 추가
import logging

app = Flask(__name__)
app.secret_key = 'julie0505!'  # 세션 암호화용

# 🚀 Redis Sentinel 클라이언트 설정
sentinel = Sentinel(
    [("redis-single-node-0.redis-single-headless.redis-single.svc.cluster.local", 26379),
     ("redis-single-node-1.redis-single-headless.redis-single.svc.cluster.local", 26379),
     ("redis-single-node-2.redis-single-headless.redis-single.svc.cluster.local", 26379)],
    socket_timeout=15,
    password="4449"  # Redis Sentinel 인증 비밀번호
)

def get_redis_master():
    try:
        host, port = sentinel.discover_master("mymaster")
        return sentinel.master_for("mymaster", socket_timeout=15, password="4449", decode_responses=True)
    except Exception as e:
        return None  # 실패 시 None 반환

# 🚀 r 변수를 동적으로 설정
r = get_redis_master()

# 🚀 MariaDB 연결 (환경에 맞게 수정)
db = pymysql.connect(
    host='my-mariadb.default.svc.cluster.local', 
    user='root', 
    password='4449', 
    db='redis_example_db', 
    charset='utf8mb4', 
    autocommit=True
)

# 🚀 로그인 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = request.cookies.get('user')
        if not user or not r.get(f"session:{user}"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



# 기본 템플릿 (회원가입/로그인 또는 신고페이지)
index_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>신고 페이지</title>
  <script>
  function updateTimer() {
    let remainingTime = {{ remaining_time }};
    let buttons = document.querySelectorAll("button[name='report_type']");
    let timerElement = document.getElementById("limit_timer");

    if (remainingTime > 0) {
      buttons.forEach(button => button.disabled = true);  // 버튼 비활성화
      timerElement.innerText = "🚨 신고 제한! " + remainingTime + "초 후 신고 가능";
      setTimeout(() => { window.location.reload(); }, remainingTime * 1000);
    }
  }
</script>
</head>
<body onload="updateTimer()">
  {% if user %}
    <div>
      <span>안녕하세요, {{ user }} 님</span>
      <a href="{{ url_for('logout') }}">로그아웃</a>
    </div>

    <h2>신고 버튼</h2>
    <p>각 신고 유형별 신고 횟수:</p>
    <ul>
      <li>경찰 신고: {{ police_count }} 회</li>
      <li>소방서 신고: {{ fire_count }} 회</li>
      <li>해경 신고: {{ coastguard_count }} 회</li>
    </ul>

    <p id="limit_timer" style="color: red;"></p>

    <form method="post" action="{{ url_for('report') }}">
      <button name="report_type" value="해경신고">해경 신고</button>
      <button name="report_type" value="소방서 신고">소방서 신고</button>
      <button name="report_type" value="경찰 신고">경찰 신고</button>
    </form>

    {% if message %}
      <p style="color: blue;">{{ message }}</p>
    {% endif %}
  {% else %}
    <div>
      <a href="{{ url_for('login') }}">로그인</a>
      <a href="{{ url_for('signup') }}">회원가입</a>
    </div>
  {% endif %}
</body>
</html>

"""

# 회원가입 페이지
signup_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>회원가입</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f4f4f9;
      color: #333;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
      width: 300px;
    }
    h2 {
      text-align: center;
      color: #4CAF50;
    }
    input {
      width: 100%;
      padding: 10px;
      margin: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    button {
      width: 100%;
      padding: 10px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover {
      background-color: #45a049;
    }
    a {
      text-decoration: none;
      color: #4CAF50;
      display: block;
      text-align: center;
      margin-top: 15px;
    }
    p {
      text-align: center;
      color: red;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>회원가입</h2>
    <form method="post">
      <input type="text" name="user" placeholder="아이디" required><br>
      <input type="password" name="password" placeholder="비밀번호" required><br>
      <button type="submit">회원가입</button>
    </form>
    <a href="{{ url_for('index') }}">홈으로</a>
    {% if message %}
      <p>{{ message }}</p>
    {% endif %}
  </div>
</body>
</html>
"""

# 로그인 페이지
login_template = """
<!doctype html>
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>로그인</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f4f4f9;
      color: #333;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
      width: 300px;
    }
    h2 {
      text-align: center;
      color: #4CAF50;
    }
    input {
      width: 100%;
      padding: 10px;
      margin: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    button {
      width: 100%;
      padding: 10px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover {
      background-color: #45a049;
    }
    a {
      text-decoration: none;
      color: #4CAF50;
      display: block;
      text-align: center;
      margin-top: 15px;
    }
    p {
      text-align: center;
      color: red;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>로그인</h2>
    <form method="post">
      <input type="text" name="user" placeholder="아이디" required><br>
      <input type="password" name="password" placeholder="비밀번호" required><br>
      <button type="submit">로그인</button>
    </form>
    <a href="{{ url_for('index') }}">홈으로</a>
    {% if message %}
      <p>{{ message }}</p>
    {% endif %}
  </div>
</body>
</html>
"""


# 🚀 회원가입 라우트 (Redis Sentinel 전용)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        try:
            with db.cursor() as cursor:
                sql = "INSERT INTO user_db (user, password) VALUES (%s, %s)"
                cursor.execute(sql, (user, password))
            session_key = f"session:{user}"
            r.set(session_key, user, ex=3*3600)  # 3시간 유효
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('user', user, max_age=3*3600)
            return resp
        except Exception as e:
            message = f"회원가입 실패: {str(e)}"
    return render_template_string(signup_template, message=message)


# 🚀 로그인 라우트 (Redis Sentinel 적용)
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        try:
            with db.cursor() as cursor:
                sql = "SELECT password FROM user_db WHERE user=%s"
                cursor.execute(sql, (user,))
                result = cursor.fetchone()
            if result and result[0] == password:
                session_key = f"session:{user}"
                r.set(session_key, user, ex=3*3600)
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie('user', user, max_age=3*3600)
                return resp
            else:
                message = "아이디 또는 비밀번호가 일치하지 않습니다."
        except Exception as e:
            message = f"로그인 중 오류: {str(e)}"
    return render_template_string(login_template, message=message)


# 🚀 로그아웃
@app.route('/logout')
@login_required
def logout():
    user = request.cookies.get('user')
    r.delete(f"session:{user}")
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('user')
    return resp

# 인덱스: 로그인 상태에 따라 다른 화면 출력
@app.route('/')
def index():
    user = request.cookies.get('user')
    message = request.args.get('message', '')

    # 각 신고 유형별 신고 횟수 가져오기
    police_count = int(r.get(f"rate:{user}:경찰 신고") or 0)
    fire_count = int(r.get(f"rate:{user}:소방서 신고") or 0)
    coastguard_count = int(r.get(f"rate:{user}:해경신고") or 0)

    # 현재 신고 제한이 걸려있는지 확인
    remaining_time = max(
        r.ttl(f"rate:{user}:경찰 신고") or 0,
        r.ttl(f"rate:{user}:소방서 신고") or 0,
        r.ttl(f"rate:{user}:해경신고") or 0
    )

    if user and r.get(f"session:{user}"):
        return render_template_string(index_template, 
                                      user=user, 
                                      message=message,
                                      police_count=police_count,
                                      fire_count=fire_count,
                                      coastguard_count=coastguard_count,
                                      remaining_time=remaining_time)
    else:
        return render_template_string(index_template, 
                                      user=None,
                                      police_count=0,
                                      fire_count=0,
                                      coastguard_count=0,
                                      remaining_time=0)


# 🚀 신고 처리 (Redis Sentinel 환경)
@app.route('/report', methods=['POST'])
@login_required
def report():
    user = request.cookies.get('user')
    report_type = request.form.get('report_type')

    rate_key = f"rate:{user}:{report_type}"  
    report_cache_key = f"report:{user}:{report_type}"  

    try:
        if r.exists(report_cache_key):
            return redirect(url_for("index", message=f"{report_type} 완료 (캐싱됨)"))

        current_count = r.incr(rate_key)

        r.setex(report_cache_key, 7200, "done")

        if current_count >= 10:
            r.expire(rate_key, 30)
            return redirect(url_for("index", message=f"🚨 신고 제한! 30초 후 다시 신고 가능"))

    except Exception as e:
        logging.error(f"❌ 신고 처리 중 오류: {e}")

    return redirect(url_for("index", message=f"{report_type} 신고 완료 (총 {current_count}회)"))


# 🚀 서버 실행
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)

