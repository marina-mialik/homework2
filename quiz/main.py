import os
from flask import Flask, request, session, redirect, url_for, render_template
from models import db, User, Quiz, Question, Option, initialize_database

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, 'db')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, 'db_quiz.db')

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SECRET_KEY'] = 'my_secret_key'

db.init_app(app)

with app.app_context():
    initialize_database()

def get_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    questions = list(quiz.questions)
    question_id = session['question_id']

    print(questions)

    try:
        desired_id = str(questions[question_id])
    except IndexError:
        desired_id = None
    
    if not desired_id:
        return None

    return quiz.questions.filter(Question.id == desired_id).first()

def get_option(question_id):
    question = Question.query.get(question_id)

    return question.options.filter_by(is_correct=True).first()

def get_quiz():
    quiz = {}

    quiz["name"] = session["new_quiz"]["name"]
    quiz["description"] = session["new_quiz"]["description"]
    quiz["questions"] = []

    for question_id in session["new_questions"].keys():
        question = session["new_questions"][question_id]
        options = []

        for option_id in range(1, 5):
            option = session["new_options"][f"{question_id}:{option_id}"]

            options.append({
                "id": option_id,
                "text": option["text"],
                "is_correct": option["is_correct"],  
            })

        quiz["questions"].append({
            "id": question_id,
            "text": question["text"],
            "options": options
        })

    return quiz

def add_empty_question():
    question_id = session["new_id"]

    session["new_questions"][f"{question_id}"] = {
        "text": ""
    }
    session.modified = True

    for option_id in range(1, 5):
        session["new_options"][f"{question_id}:{option_id}"] = {
            "text": "",
            "is_correct": option_id == 1
        }
        session.modified = True

@app.route('/', methods = ['GET'])
def index():
    quizzes = Quiz.query.all()

    return render_template('index.html', quizzes=quizzes)

@app.route("/quiz/overview/<int:quiz_id>/", methods = ["GET"])
def quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)

    if session.get('question_id'):
        session['question_id'] = 0
    
    if session.get('answer_counter'):
        session['answer_counter'] = 0

    return render_template('quiz.html', quiz=quiz)

@app.route("/quiz/progress/<int:quiz_id>/", methods = ["GET", "POST"])
def question(quiz_id=0):
    if not session.get('question_id'):
        session['question_id'] = 0
    
    if not session.get('answer_counter'):
        session['answer_counter'] = 0

    question = get_question(quiz_id)

    if request.method == "POST":
        form = request.form.to_dict()
        correct_option = get_option(question.id)
        is_correct = str(correct_option.id) in form.values()

        session["question_id"] = session["question_id"] + 1
        session.modified = True

        if is_correct:
            session['answer_counter'] = session['answer_counter'] + 1
            session.modified = True

    question = get_question(quiz_id)

    if not question:
        return redirect(url_for('result', quiz_id=quiz_id))

    return render_template('question.html',
        quiz_id=quiz_id,
        question=question,
    )

@app.route("/quiz/result/<int:quiz_id>/", methods = ["GET"])
def result(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    result = f"{session["answer_counter"]} / {len(list(quiz.questions))}"

    return render_template('result.html', quiz=quiz, result=result)
    

@app.route("/quiz/delete/<int:quiz_id>", methods = ["GET", "POST"])
def delete(quiz_id):
    quiz = Quiz.query.get(quiz_id)

    if request.method == "POST" and request.form.get('yes'):
        db.session.delete(quiz)
        db.session.commit()

        return render_template('delete.html', quiz_id=None, quiz=quiz)
    
    if request.method == "POST" and request.form.get('no'):
        return redirect(url_for('index'))

    return render_template('delete.html', quiz_id=quiz_id, quiz=quiz)

@app.route("/quiz/edit/<int:quiz_id>/", methods = ["GET", "POST"])
def edit(quiz_id):
    quiz = Quiz.query.get(quiz_id)

    if request.method == "POST":
        form = request.form.to_dict()

        for key in form.keys():
            if "question" in key:
                _name, id = key.split(":")
                question = Question.query.get(id)
                question.text = form.get(key) or "question"
                continue

            if "option" in key:
                _name, id = key.split(":")
                option = Option.query.get(id)
                option.text = form.get(key) or "option"
                continue

            if "answer" in key:
                _name, question_id = key.split(":")
                question = Question.query.get(question_id)
                option = question.options.filter_by(is_correct=True).first()
                option.is_correct = False
                
                option = Option.query.get(id)
                option.is_correct = True

            quiz.name = form.get("name") or "name"
            quiz.description = form.get("description") or "description"

        db.session.commit()
        return render_template('edit.html', quiz_id=None, quiz=quiz)

    return render_template('edit.html', quiz_id=quiz_id, quiz=quiz)

@app.route("/quiz/create/", methods = ["GET", "POST"])
def create():
    if not session.get("new_id"):
        session["new_id"] = 1

    if not session.get("new_quiz"):
        session["new_quiz"] = {
            "name": "",
            "description": "",
        }
        session.modified = True

    if not session.get("new_questions"):
        session["new_questions"] = {
            "1": {
                "text": "",
            }
        }
        session.modified = True

    if not session.get("new_options"):
        session["new_options"] = {
            "1:1": {
                "text": "",
                "is_correct": True
            },
            "1:2": {
                "text": "",
                "is_correct": False
            },
            "1:3": {
                "text": "",
                "is_correct": False
            },
            "1:4": {
                "text": "",
                "is_correct": False
            }
        }

    if request.method == "POST" and request.form.get('cancel'):
        session["new_id"] = 1
        session["new_quiz"] = {}
        session["new_questions"] = {}
        session["new_options"] = {}

        return redirect(url_for('index'))
    
    if request.method == "POST" and request.form.get('create'):
        form = request.form.to_dict()

        for key in form.keys():
            if "question" in key:
                _name, id = key.split(":")
                question = session["new_questions"][id]
                question["text"] = form.get(key)

                session.modified = True
                continue

            if "option" in key:
                _name, question_id, option_id = key.split(":")
                option = session["new_options"][f"{question_id}:{option_id}"]
                option["text"] = form.get(key)

                session.modified = True
                continue

            if "answer" in key:
                _name, question_id = key.split(":")
                option_id = form.get(key)
                option = session["new_options"][f"{question_id}:{option_id}"]
                option["is_correct"] = True

                session.modified = True
                continue

            session["new_quiz"]["name"] = form.get("name")
            session["new_quiz"]["description"] = form.get("description")

        tmp_quiz = get_quiz()
        user = User.query.first()
        questions = []
        quiz = Quiz(name=tmp_quiz["name"], author=user, description=tmp_quiz["description"])

        for question in tmp_quiz["questions"]:
            options = []

            for option in question["options"]:
                options.append(Option(text=option["text"], is_correct=option["is_correct"]))

            questions.append(Question(text=question["text"], options=options))

        quiz.questions.extend(questions)
        db.session.add_all([user])
        db.session.add_all([quiz])
        db.session.add_all(questions)
        
        for question in questions:
            print(question.options)
            db.session.add_all(question.options)
        
        db.session.commit()

        session["new_id"] = 1
        session["new_quiz"] = {}
        session["new_questions"] = {}
        session["new_options"] = {}

        return render_template('create.html', quiz=quiz, quiz_id=None)

    if request.method == "POST" and request.form.get('add'):
        form = request.form.to_dict()

        for key in form.keys():
            if "question" in key:
                _name, id = key.split(":")
                question = session["new_questions"][id]
                question["text"] = form.get(key)

                session.modified = True
                continue

            if "option" in key:
                _name, question_id, option_id = key.split(":")
                option = session["new_options"][f"{question_id}:{option_id}"]
                option["text"] = form.get(key)

                session.modified = True
                continue

            if "answer" in key:
                _name, question_id = key.split(":")
                option_id = form.get(key)
                option = session["new_options"][f"{question_id}:{option_id}"]
                option["is_correct"] = True

                session.modified = True
                continue

            session["new_quiz"]["name"] = form.get("name")
            session["new_quiz"]["description"] = form.get("description")

        session["new_id"] = session["new_id"] + 1
        add_empty_question()

    quiz = get_quiz()
    return render_template('create.html', quiz=quiz, quiz_id=session["new_id"])

@app.errorhandler(404)
def page_not_found(error):
    return render_template('not-found.html', error=error)

app.run(debug=True, host='0.0.0.0', port=5550)