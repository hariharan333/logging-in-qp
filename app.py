from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from github import Github
import os,requests,json

app = Flask(__name__)
CORS(app)

#Add log files and logging format
FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = "my_app.log"

#Dot env added
APP_ROOT = os.path.dirname(__file__)   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

#SQLalchemy
app.config.from_object(os.getenv('APP_SETTINGS'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Importing Model
from models import Question
from models import Book


#Flask admin panel
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='Team Tomato', template_mode='bootstrap3')

#Flask admin model views
admin.add_view(ModelView(Question, db.session))
admin.add_view(ModelView(Book, db.session))

# Mail settings

mail_settings = {
  "MAIL_SERVER": 'smtp.gmail.com',
  "MAIL_PORT": 465,
  "MAIL_USE_TLS": False,
  "MAIL_USE_SSL": True,
  "MAIL_USERNAME": os.getenv('EMAIL_USER'),
  "MAIL_PASSWORD": os.getenv('EMAIL_PASSWORD')
}
print(os.getenv('EMAIL_PASSWORD'))
print(os.getenv('EMAIL_USER'))
app.config.update(mail_settings)
mail = Mail(app)


# Create of logger and file handler
def get_logger(logger_name):
   logger = logging.getLogger(logger_name)
   logger.setLevel(logging.DEBUG)
   logger.addHandler(get_file_handler())
   logger.propagate = False
   return logger
def get_file_handler():
   file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
   file_handler.setFormatter(FORMATTER)
   return file_handler

# Question API

@app.route("/", methods=['GET'])
def get():
  mylogger = get_logger("home page")
  mylogger.info(request.remote_addr)
  return "<h1>Team Tomato welcome you</h1>"

@app.route("/api/v1/question/add", methods=['POST'])
def add_question():
  mylogger = get_logger("add_question")
  mylogger.info(request.remote_addr)

  question_data = request.get_json()['question']

  subjectName = question_data['subjectName']
  shortForm = question_data['shortForm']
  staff = question_data['staff']
  year = question_data['year']
  url = question_data['url']

  try:
    question=Question(
        subjectName = subjectName,
        shortForm = shortForm,
        staff = staff,
        year = year,
        url = url
    )
    db.session.add(question)
    db.session.commit()
    res = {
      'id': question.id,
      'subjectName': question.subjectName,
      'shortForm': question.shortForm,
      'staff': question.staff,
      'year': question.year,
      'url': question.url
    }
    return jsonify(res)
  except Exception as e:
    return(str(e))

@app.route("/api/v1/question", methods=['GET'])
def get_all_questions():
  mylogger = get_logger("get_all_questions")
  mylogger.info(request.remote_addr)

  try:
    questions = Question.query.all()
    return  jsonify([e.serialize() for e in questions])
  except Exception as e:
    return(str(e))

@app.route("/api/v1/question/<id_>", methods=['GET'])
def get_question_by_id(id_):
  mylogger = get_logger("get_question_by_id")
  mylogger.info(request.remote_addr)

  try:
    question = Question.query.filter_by(id=id_).first()
    return jsonify(question.serialize())
  except Exception as e:
    return(str(e))

@app.route("/api/v1/question/search", methods=['GET'])
def search_question():
  mylogger = get_logger("search_question")
  mylogger.info(request.remote_addr)
  try:
    search_str = "%"+request.args.get('search_str')+"%"
    questions = Question.query.filter(or_(Question.subjectName.ilike(search_str), Question.staff.ilike(search_str), Question.shortForm.ilike(search_str)))
    return  jsonify([e.serialize() for e in questions])
  except Exception as e:
    return(str(e))


#Contact Us API

@app.route("/api/v1/contactus", methods=['POST'])
def contact_us():
  mylogger = get_logger("contact_us")
  mylogger.info(request.remote_addr)
  try:
    contact_data = request.get_json()['contact']
    name = contact_data['name']
    email = contact_data['email']
    message = contact_data['message']
    __send_email(os.getenv('EMAIL_SUB'), email, message)
    res = {
        'status': "Submission successful",
        'name': name,
        'email': email,
        'message': message
    }
    return jsonify(res)
  except Exception as e:
    return (str(e)) 

def __send_email(sub, recipient_list, message):
  msg = Message(subject=sub,
              sender = (os.getenv('MAIL_SENDER_NAME'), app.config.get("MAIL_USERNAME")),
              recipients = [os.getenv("RECEIVER_MAIL")],
              body = "From: "+recipient_list+" --- Message: "+message)
  mail.send(msg)


# GITHUB Contributors API

@app.route("/api/v1/github/contributors", methods=["GET"])
def githubRepoDetails():
    mylogger = get_logger("githubRepoDetails")
    mylogger.info(request.remote_addr)
    g = Github()
    details=[]
    try:
        pulls=0
        commits=0
        conts=0
        print("start")
        for repo in g.get_user(os.getenv("GITHUB_USER_NAME")).get_repos():
            repo1 = g.get_repo(repo.full_name)
            pulls += repo1.get_pulls().totalCount
            commits += repo1.get_commits().totalCount
            conts += repo1.get_contributors().totalCount
        details.append(dict([("Name: ", "Team-Tomato"), ("Pull Requests: ", pulls), ("Commits: ", commits), ("Contributors: ", conts)]))
        return jsonify(details)
    except Exception as e:
        return(str(e))


# Books API

@app.route('/api/v1/book/add', methods=['POST'])
def add_book():
  mylogger = get_logger("add_book")
  mylogger.info(request.remote_addr)

  book_data = request.get_json()['book']
  title = book_data['title']
  author = book_data['author']
  publisher = book_data['publisher']
  isbn = book_data['isbn']
  url = book_data['url']

  try:
    book = Book(
        title = title,
        author = author,
        publisher = publisher,
        isbn = isbn,
        url = url
    )
    db.session.add(book)
    db.session.commit()
    res = {
      'id': book.id,
      'title': book.title,
      'author': book.author,
      'publisher': book.publisher,
      'isbn': book.isbn,
      'url': book.url
    }
    return jsonify(res)
  except Exception as e:
    return(str(e))

@app.route("/api/v1/book/all", methods=['GET'])
def get_all_books():
    mylogger = get_logger("get_all_books")
    mylogger.info(request.remote_addr)

    try:
        books = Book.query.all()
        return jsonify([e.serialize() for e in books])
    except Exception as e:
        return str(e)


@app.route("/api/v1/book/search", methods=['GET'])
def search_book():
    mylogger = get_logger("search_book")
    mylogger.info(request.remote_addr)

    try:
        search_str = "%" + request.args.get('search_str') + "%"
        books = Book.query.filter(or_(Book.author.ilike(search_str), Book.title.ilike(search_str), Book.publisher.ilike(search_str)))
        print(books)
        return jsonify([e.serialize() for e in books])
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run()
