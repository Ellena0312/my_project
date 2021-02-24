from flask import Flask, render_template, jsonify, request  # 웹서버를 시작하는 파이썬 파일

# 얘는 항상 켜져있어야해 (위의 빨간 네모가 실행중임을 의미)
app = Flask(__name__)

@app.route('/')  # / 를 라우트라고 부름. (/ 하나면 루트) 웹서버에 여러 기능을 해줄 수 있도록함
def home():  # 얘는 함수를 실행하려면 라우트로 요청하면 돼 따로 호출없음
    return render_template('wishlist_home.html')

@app.route('/show_mine')
def show_mine():
    return render_template('wishlist_show_mine.html')

