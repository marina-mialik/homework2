import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from models import User, Quiz, Question, Option, SessionLocal, initialize_database

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, 'db')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="my_secret_key",
    session_cookie="session"
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

initialize_database()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_question(request: Request, quiz_id: int, db: Session):
    quiz = db.query(Quiz).get(quiz_id)
    questions = list(quiz.questions)
    question_id = request.session.get('question_id', 0)

    try:
        desired_id = str(questions[question_id].id)
    except IndexError:
        desired_id = None
    
    if not desired_id:
        return None

    return db.query(Question).filter(Question.id == desired_id).first()

def get_option(question_id: int, db: Session):
    return db.query(Option).filter(Option.question_id == question_id, Option.is_correct == True).first()

def get_quiz(request: Request):
    quiz = {}

    quiz["name"] = request.session.get("new_quiz", {}).get("name", "")
    quiz["description"] = request.session.get("new_quiz", {}).get("description", "")
    quiz["questions"] = []

    new_questions = request.session.get("new_questions", {})
    new_options = request.session.get("new_options", {})

    for question_id in new_questions.keys():
        question = new_questions[question_id]
        options = []

        for option_id in range(1, 5):
            option = new_options.get(f"{question_id}:{option_id}", {})
            options.append({
                "id": option_id,
                "text": option.get("text", ""),
                "is_correct": option.get("is_correct", option_id == 1),  
            })

        quiz["questions"].append({
            "id": question_id,
            "text": question.get("text", ""),
            "options": options
        })

    return quiz

def add_empty_question(request: Request):
    question_id = request.session.get("new_id", 1)
    
    if "new_questions" not in request.session:
        request.session["new_questions"] = {}
    if "new_options" not in request.session:
        request.session["new_options"] = {}

    request.session["new_questions"][f"{question_id}"] = {"text": ""}

    for option_id in range(1, 5):
        request.session["new_options"][f"{question_id}:{option_id}"] = {
            "text": "",
            "is_correct": option_id == 1
        }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    quizzes = db.query(Quiz).all()
    return templates.TemplateResponse("index.html", {"request": request, "quizzes": quizzes})

@app.get("/quiz/overview/{quiz_id}/", response_class=HTMLResponse)
async def quiz(request: Request, quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).get(quiz_id)

    if 'question_id' in request.session:
        request.session['question_id'] = 0
    
    if 'answer_counter' in request.session:
        request.session['answer_counter'] = 0

    return templates.TemplateResponse("quiz.html", {"request": request, "quiz": quiz})

@app.get("/quiz/progress/{quiz_id}", response_class=HTMLResponse)
@app.post("/quiz/progress/{quiz_id}", response_class=HTMLResponse)
async def question(request: Request, quiz_id: int, db: Session = Depends(get_db)):
    if 'question_id' not in request.session:
        request.session['question_id'] = 0
    
    if 'answer_counter' not in request.session:
        request.session['answer_counter'] = 0

    current_question = get_question(request, quiz_id, db)

    if request.method == "POST":
        form_data = await request.form()
        correct_option = get_option(current_question.id, db)
        is_correct = str(correct_option.id) in form_data.values()

        request.session["question_id"] = request.session["question_id"] + 1

        if is_correct:
            request.session['answer_counter'] = request.session['answer_counter'] + 1

    current_question = get_question(request, quiz_id, db)

    if not current_question:
        return RedirectResponse(url=f"/quiz/result/{quiz_id}/", status_code=303)

    return templates.TemplateResponse("question.html", {
        "request": request,
        "quiz_id": quiz_id,
        "question": current_question,
    })

@app.get("/quiz/result/{quiz_id}/", response_class=HTMLResponse)
async def result(request: Request, quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).get(quiz_id)
    result = f"{request.session.get('answer_counter', 0)} / {len(list(quiz.questions))}"

    return templates.TemplateResponse("result.html", {
        "request": request, 
        "quiz": quiz, 
        "result": result
    })

@app.get("/quiz/delete/{quiz_id}", response_class=HTMLResponse)
@app.post("/quiz/delete/{quiz_id}", response_class=HTMLResponse)
async def delete(request: Request, quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).get(quiz_id)

    if request.method == "POST":
        form_data = await request.form()
        if 'yes' in form_data:
            db.delete(quiz)
            db.commit()
            return templates.TemplateResponse("delete.html", {
                "request": request, 
                "quiz_id": None, 
                "quiz": quiz
            })
        if 'no' in form_data:
            return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("delete.html", {
        "request": request, 
        "quiz_id": quiz_id, 
        "quiz": quiz
    })

@app.get("/quiz/edit/{quiz_id}", response_class=HTMLResponse)
@app.post("/quiz/edit/{quiz_id}", response_class=HTMLResponse)
async def edit(request: Request, quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).get(quiz_id)

    if request.method == "POST":
        form_data = await request.form()
        
        for key in form_data.keys():
            if "question" in key:
                _name, id = key.split(":")
                question = db.query(Question).get(id)
                question.text = form_data.get(key) or "question"
                continue

            if "option" in key:
                _name, id = key.split(":")
                option = db.query(Option).get(id)
                option.text = form_data.get(key) or "option"
                continue

            if "answer" in key:
                _name, question_id = key.split(":")
                question = db.query(Question).get(question_id)
                old_option = db.query(Option).filter(
                    Option.question_id == question_id, 
                    Option.is_correct == True
                ).first()
                if old_option:
                    old_option.is_correct = False
                
                option_id = form_data.get(key)
                new_option = db.query(Option).get(option_id)
                if new_option:
                    new_option.is_correct = True

            quiz.name = form_data.get("name") or "name"
            quiz.description = form_data.get("description") or "description"

        db.commit()
        return templates.TemplateResponse("edit.html", {
            "request": request, 
            "quiz_id": None, 
            "quiz": quiz
        })

    return templates.TemplateResponse("edit.html", {
        "request": request, 
        "quiz_id": quiz_id, 
        "quiz": quiz
    })

@app.get("/quiz/create/", response_class=HTMLResponse)
@app.post("/quiz/create/", response_class=HTMLResponse)
async def create(request: Request, db: Session = Depends(get_db)):
    if "new_id" not in request.session or not bool(request.session.get("new_id")):
        request.session["new_id"] = 1

    if "new_quiz" not in request.session or not not bool(request.session.get("new_quiz")):
        request.session["new_quiz"] = {
            "name": "",
            "description": "",
        }

    if "new_questions" not in request.session or not bool(request.session.get("new_questions")):
        request.session["new_questions"] = {
            "1": {
                "text": "",
            }
        }

    if "new_options" not in request.session or not bool(request.session.get("new_options")):
        request.session["new_options"] = {
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

    if request.method == "POST":
        form_data = await request.form()
        
        if 'cancel' in form_data:
            request.session["new_id"] = 1
            request.session["new_quiz"] = {}
            request.session["new_questions"] = {}
            request.session["new_options"] = {}
            return RedirectResponse(url="/", status_code=303)
        
        if 'create' in form_data:
            for key in form_data.keys():
                if "question" in key:
                    _name, id = key.split(":")
                    question = request.session["new_questions"][id]
                    question["text"] = form_data.get(key)
                    continue

                if "option" in key:
                    _name, question_id, option_id = key.split(":")
                    option = request.session["new_options"][f"{question_id}:{option_id}"]
                    option["text"] = form_data.get(key)
                    continue

                if "answer" in key:
                    _name, question_id = key.split(":")
                    option_id = form_data.get(key)
                    option = request.session["new_options"][f"{question_id}:{option_id}"]
                    option["is_correct"] = True
                    continue

                request.session["new_quiz"]["name"] = form_data.get("name")
                request.session["new_quiz"]["description"] = form_data.get("description")

            tmp_quiz = get_quiz(request)
            user = db.query(User).first()
            questions = []
            quiz = Quiz(name=tmp_quiz["name"], author=user, description=tmp_quiz["description"])

            for question in tmp_quiz["questions"]:
                options = []

                for option in question["options"]:
                    options.append(Option(text=option["text"], is_correct=option["is_correct"]))

                questions.append(Question(text=question["text"], options=options))

            quiz.questions.extend(questions)
            db.add_all([user])
            db.add_all([quiz])
            db.add_all(questions)
            
            for question in questions:
                db.add_all(question.options)
            
            db.commit()

            request.session["new_id"] = 1
            request.session["new_quiz"] = {}
            request.session["new_questions"] = {}
            request.session["new_options"] = {}

            return templates.TemplateResponse("create.html", {
                "request": request, 
                "quiz": quiz, 
                "quiz_id": None
            })

        if 'add' in form_data:
            for key in form_data.keys():
                if "question" in key:
                    _name, id = key.split(":")
                    question = request.session["new_questions"][id]
                    question["text"] = form_data.get(key)
                    continue

                if "option" in key:
                    _name, question_id, option_id = key.split(":")
                    option = request.session["new_options"][f"{question_id}:{option_id}"]
                    option["text"] = form_data.get(key)
                    continue

                if "answer" in key:
                    _name, question_id = key.split(":")
                    option_id = form_data.get(key)
                    option = request.session["new_options"][f"{question_id}:{option_id}"]
                    option["is_correct"] = True
                    continue

                request.session["new_quiz"]["name"] = form_data.get("name")
                request.session["new_quiz"]["description"] = form_data.get("description")

            request.session["new_id"] = request.session["new_id"] + 1
            add_empty_question(request)

    quiz = get_quiz(request)
    return templates.TemplateResponse("create.html", {
        "request": request, 
        "quiz": quiz, 
        "quiz_id": request.session.get("new_id", 1)
    })

@app.exception_handler(404)
async def page_not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse("not-found.html", {
        "request": request, 
        "error": exc
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5555)