from flask_sqlalchemy import SQLAlchemy
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
import json

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True
    __allow_unmapped__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {column.name: getattr(self, column.name) 
                for column in self.__table__.columns}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class User(BaseModel):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(25), nullable=False, unique=True)
    quizzes: Mapped[List['Quiz']] = relationship(
        'Quiz', 
        backref='author', 
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __init__(self, name: str) -> None:
        self.name = name

class Quiz(BaseModel):
    __tablename__ = 'quizzes'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(200))
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    questions: Mapped[List['Question']] = relationship(
        'Question',
        secondary='quiz_question',
        back_populates='quizzes',
        lazy='dynamic'
    )

    def __init__(self, name: str, author: User, description: Optional[str] = None) -> None:
        self.name = name
        self.author = author
        self.description = description

    def __repr__(self) -> str:
        return f'{self.id}'

class Question(BaseModel):
    __tablename__ = 'questions'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    text: Mapped[str] = mapped_column(db.String(250), nullable=False)
    
    options: Mapped[List['Option']] = relationship(
        'Option', 
        back_populates='question', 
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    quizzes: Mapped[List['Quiz']] = relationship(
        'Quiz',
        secondary='quiz_question',
        back_populates='questions',
        lazy='dynamic'
    )

    def __init__(self, text: str, options: Optional[List['Option']] = None) -> None:
        self.text = text
        if options:
            self.options = options

    def __repr__(self) -> str:
        return f'{self.id}'

class Option(BaseModel):
    __tablename__ = 'options'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    text: Mapped[str] = mapped_column(db.String(250), nullable=False)
    is_correct: Mapped[bool] = mapped_column(db.Boolean, default=False)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    question: Mapped['Question'] = relationship(
        'Question', 
        back_populates='options'
    )

    def __init__(self, text: str, is_correct: bool = False, question: Optional['Question'] = None) -> None:
        self.text = text
        self.is_correct = is_correct
        if question:
            self.question = question

    def __repr__(self) -> str:
        return f'{self.id}'

quiz_question = db.Table(
    'quiz_question',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quizzes.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True)
)

def initialize_database():
    db.drop_all()
    db.create_all()
    
    user1 = User(name='user1')
    user2 = User(name='user2')
    
    quiz1 = Quiz(name='Еда и кулинария', author=user1, description="Отправься в вкусное путешествие по миру кулинарии – от древних традиций до современных гастрономических шедевров! Эта аппетитная викторина с хитринкой проверит не только твои знания о еде, но и умение отличать мифы от кулинарных фактов.")
    quiz2 = Quiz(name='География и путешествия', author=user1, description="Отправляйся в увлекательное путешествие по континентам, странам и природным чудесам – без билета и чемодана! ✈️ Эта викторина – разной сложности: от известных фактов до каверзных загадок. Выбирай правильный ответ среди хитрых вариантов и узнай, насколько хорошо ты знаешь нашу планету.")
    quiz3 = Quiz(name='Кино и сериалы', author=user2, description="Любишь фильмы и сериалы? Сможешь угадать культовые сцены, цитаты и малоизвестные факты? Тогда эта викторина для тебя! Что тебя ждет? Вопросы разной сложности – от блокбастеров до нишевого кино Хитрые варианты ответов, которые заставят задуматься. Факты, которые удивят даже киноманов")
    quiz4 = Quiz(name='Музыкальный микс', author=user2, description="Любишь музыку от классики до современных хитов? Проверь, сможешь ли ты узнать исполнителей, треки и интересные факты из мира музыки!")

    options1 = [
        Option(text='Морковь'),
        Option(text='Картофель', is_correct=True),
        Option(text='Капуста'),
        Option(text='Свёкла')
    ]
    
    options2 = [
        Option(text='Гаспачо'),
        Option(text='Минестроне'),
        Option(text='Буйабес', is_correct=True),
        Option(text='Том-ям')
    ]
    
    options3 = [
        Option(text='Перец'),
        Option(text='Чеснок'),
        Option(text='Соль', is_correct=True),
        Option(text='Мёд')
    ]
    
    options4 = [
        Option(text='Брынза', is_correct=True),
        Option(text='Пармезан'),
        Option(text='Моцарелла'),
        Option(text='Гауда')
    ]
    
    options5 = [
        Option(text='Гибралтарский'),
        Option(text='Босфор', is_correct=True),
        Option(text='Магелланов'),
        Option(text='Дарданеллы')
    ]
    
    options6 = [
        Option(text='Рио-де-Жанейро', is_correct=True),
        Option(text='Лима'),
        Option(text='Сантьяго'),
        Option(text='Буэнос-Айрес')
    ]
    
    options7 = [
        Option(text='Африка'),
        Option(text='Южная Америка'),
        Option(text='Антарктида', is_correct=True),
        Option(text='Австралия')
    ]
    
    options8 = [
        Option(text='Сидней'),
        Option(text='Брисбен'),
        Option(text='Мельбурн'),
        Option(text='Канберра', is_correct=True)
    ]

    options9 = [
        Option(text='«Звёздные войны» (1977)'),
        Option(text='«Кинг-Конг» (1933)', is_correct=True),
        Option(text='«Терминатор 2» (1991)'),
        Option(text='«Парк Юрского периода» (1993)')
    ]

    options10 = [
        Option(text='Титаник', is_correct=True),
        Option(text='Властелин колец: Возвращение короля'),
        Option(text='Бен-Гур'),
        Option(text='Ла-Ла Ленд')
    ]

    options11 = [
        Option(text='Аватар', is_correct=True),
        Option(text='Мстители: Финал'),
        Option(text='Титаник'),
        Option(text='Звёздные войны: Пробуждение силы')
    ]

    options12 = [
        Option(text='Очень странные дела'),
        Option(text='Бумажный дом'),
        Option(text='Ведьмак'),
        Option(text='Игра в кальмара', is_correct=True)
    ]

    options13 = [
        Option(text='Пол Маккартни'),
        Option(text='Боб Дилан', is_correct=True),
        Option(text='Мик Джаггер'),
        Option(text='Дэвид Боуи')
    ]

    options14 = [
        Option(text='The Rolling Stones'),
        Option(text='Pink Floyd'),
        Option(text='Led Zeppelin'),
        Option(text='Queen', is_correct=True)
    ]

    options15 = [
        Option(text='Элвис Пресли'),
        Option(text='Майкл Джексон', is_correct=True),
        Option(text='Принц'),
        Option(text='Джордж Майкл')
    ]

    options16 = [
        Option(text='Диско'),
        Option(text='Рок-н-ролл'),
        Option(text='Джаз'),
        Option(text='Техно', is_correct=True)
    ]

    questions = [
        Question(text='Какой овощ называют «вторым хлебом»?', options=options1),
        Question(text='Как называется французский суп из морепродуктов?', options=options2),
        Question(text='Что в Древнем Египте использовали как деньги?', options=options3),
        Question(text='Какой сыр готовят из овечьего молока и выдерживают в рассоле?', options=options4),
        Question(text='Какой пролив разделяет Европу и Азию?', options=options5),
        Question(text='В каком городе находится статуя Христа-Искупителя?', options=options6),
        Question(text='Какой материк самый сухой?', options=options7),
        Question(text='Столица Австралии — это...', options=options8),
        Question(text='Какой фильм стал первым в истории, получившим «Оскар» за лучшие визуальные эффекты?', options=options9),
        Question(text='Какой фильм получил больше всего «Оскаров» за всю историю?', options=options10),
        Question(text='Какой фильм стал самым кассовым в истории (без учёта инфляции)?', options=options11),
        Question(text='Какой сериал Netflix стал самым популярным за первые 28 дней после выхода?', options=options12),
        Question(text='Кто получил Нобелевскую премию по литературе в 2016 году, будучи известным музыкантом?', options=options13),
        Question(text='Какая группа исполнила легендарную песню «Bohemian Rhapsody»?', options=options14),
        Question(text='Кто считается «королём поп-музыки»?', options=options15),
        Question(text='Какой музыкальный стиль родился в Детройте в 1980-х?', options=options16)
    ]

    quiz1.questions.extend(questions[:4])
    quiz2.questions.extend(questions[4:8])
    quiz3.questions.extend(questions[8:12])
    quiz4.questions.extend(questions[12:])

    db.session.add_all([user1, user2])
    db.session.add_all([quiz1, quiz2, quiz3, quiz4])
    db.session.add_all(questions)
    
    for question in questions:
        db.session.add_all(question.options)
    
    db.session.commit()
