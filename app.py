# from flask import Flask, render_template, jsonify, request  # 웹서버를 시작하는 파이썬 파일

import jwt
import datetime
import hashlib
import requests
from functools import wraps
from bs4 import BeautifulSoup
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request, redirect, url_for, g

# 얘는 항상 켜져있어야해 (위의 빨간 네모가 실행중임을 의미)
app = Flask(__name__)

# mongodb
client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://test:test@localhost',27017)
db = client.dbsparta

# jwt secret key
SECRET_KEY = 'hello world'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 쿠키에서 token_give 가져오기
        token_receive = request.cookies.get('token_give')
        print('token_receive :', token_receive)

        if token_receive is None:
            # token이 없는 경우
            return redirect(url_for('login'))

        try:
            # 전달받은 token이 위조되었는지 확인 (단방향이기 때문에 비밀번호와 마찬가지로 해쉬처리하여 동일한지 비교)
            # SECRET_KEY를 모르면 동일한 해쉬를 만들 수 없음
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            # 토큰 없거나 만료되었거나 올바르지 않은 경우 로그인 페이지로 이동
            return redirect(url_for('login'))

        # g는 각각의 request 내에서만 값이 유효한 스레드 로컬 변수입니다.
        # 사용자의 요청이 동시에 들어오더라도 각각의 request 내에서만 g 객체가 유효하기 때문에 사용자 ID를 저장해도 문제가 없습니다.
        g.user = db.wish_note_user.find_one({'id': payload["id"]})

        # 로그인 성공시 다음 함수 실행
        return f(*args, **kwargs)

    return decorated_function


#################################
# HTML 응답 API
#################################


@app.route('/')
@login_required
def home():
    return render_template('temp_show_mine.html', user=g.user)


@app.route('/login')  # / 를 라우트라고 부름. (/ 하나면 루트) 웹서버에 여러 기능을 해줄 수 있도록함
def login():  # 얘는 함수를 실행하려면 라우트로 요청하면 돼 따로 호출없음
    return render_template('temp_login.html')


@app.route('/register')
def register():
    return render_template('temp_register.html')


#################################
# JSON 응답 API
#################################


# 회원가입
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    name_receive = request.form['name_give']
    address_receive = request.form['address_give']

    # id 중복 확인
    user = db.wish_note_user.find_one({'id': id_receive})
    if user is not None:
        return jsonify({'result': 'fail', 'msg': '아이디가 중복되었습니다'})

    # pw를 sha256 방법(단방향)으로 암호화
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.wish_note_user.insert_one({'id': id_receive,
                                  'pw': pw_hash,
                                  'name': name_receive,
                                  'address': address_receive})

    return jsonify({'result': 'success', 'msg': '회원 가입을 축하합니다'})


# 로그인
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # pw를 sha256 방법(단방향)으로 암호화
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된 pw을 가지고 해당 유저를 찾기
    user = db.wish_note_user.find_one({'id': id_receive, 'pw': pw_hash})

    if user is not None:
        # jwt 토큰 발급
        payload = {
            'id': user['id'],  # user id
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 만료 시간 (1일 뒤 만료)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print(f'token : {token}')

        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디와 비밀번호를 확인해주세요'})


# db에 리스트 넣기
@app.route('/memo_list', methods=['POST'])
def post_list():
    # 1. 클라이언트로부터 데이터를 받기
    user_receive = request.form['user_give']
    name_receive = request.form['name_give']
    price_receive = request.form['price_give']
    rank_receive = request.form['rank_give']
    url_receive = request.form['url_give']  # 클라이언트로부터 url을 받는 부분
    comment_receive = request.form['comment_give']  # 클라이언트로부터 comment를 받는 부분

    # 2. meta tag를 스크래핑하기
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    og_image = soup.select_one('meta[property="og:image"]')
    og_title = soup.select_one('meta[property="og:title"]')
    og_description = soup.select_one('meta[property="og:description"]')

    # url_title = og_title['content']
    # url_description = og_description['content']
    # url_image = og_image['content']

    if og_title is not None:
        url_title = og_title['content']
    else:
        url_title = 'og tag가 없습니다.'
    if og_image is not None:
        url_image = og_image['content']
    else:
        url_image = 'https://i.pinimg.com/originals/ae/8a/c2/ae8ac2fa217d23aadcc913989fcc34a2.png'
    if og_image is not None:
        url_description = og_description['content']
    else:
        url_description = 'og desc가 없습니다.'

    wish_list = {'user': user_receive,
                 'name': name_receive,
                 'price': price_receive,
                 'rank': rank_receive,
                 'comment': comment_receive,
                 'url': url_receive,
                 'title': url_title,
                 'desc': url_description,
                 'image': url_image}

    # 3. mongoDB에 데이터를 넣기
    # user_check = db.wish_note_list.find_one({'user': user_receive})
    # if user_check is not None:
    #     return
    # else:
    db.wish_note_list.insert_one(wish_list)
    return jsonify({'result': 'success'})


# db에서 리스트 가져오기
@app.route('/memo_list', methods=['GET'])
def read_list():
    user_receive = request.args.get('user_give')
    # 1. mongoDB에서 user가 user_receive와 같은 모든 데이터 조회해오기 (Read)
    result = list(db.wish_note_list.find({'user': user_receive}, {'_id': False}))
    # 2. wish_list라는 키 값으로 wish_note_list 정보 보내주기
    return jsonify({'result': 'success', 'wish_list': result})


#

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
