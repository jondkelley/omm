# using python 3
from flask import Flask, render_template, make_response, request, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField,  FormField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired
import json
import sqlite3
import uuid
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
Bootstrap(app) # Flask-Bootstrap requires this line
app.config['BOOTSTRAP_SERVE_LOCAL'] = True


# with Flask-WTF, each web form is represented by a class
# "NameForm" can change; "(FlaskForm)" cannot
# see the route for "/" and "index.html" to see how this is used

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

class SqliteDb():
    """
    helpers for sqlite
    """
    def does_user_exist_in_survey(self, qao, username, survey_id):
        """
        validate if user already voted in a survey
        """
        return qao.execute("SELECT * FROM voter_registry WHERE username=? AND survey_id=?", (username, survey_id))

    def sss(self, qao, username, survey_id):
        """
        validate if user already voted in a survey
        """
        return qao.execute("SELECT * FROM voter_registry WHERE username=? AND survey_id=?", (username, survey_id))

class JsonDb():
    """
    interact with the local json database
    """
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        """
        load db from disk into data dictionary
        """
        with open('matrix.db') as f:
            self.data = json.load(f)
            #print(json.dumps(self.data, indent=3))

    def write(self):
        """
        write db to disk
        """
        with open('matrix.db', 'w') as outfile:
            json.dump(self.data, outfile)

    def get_orgname(self):
        """
        retrieve the org name
        """
        return self.data['organization_name']

    def validate_question(self, dimension, level, question_id):
        """
        returns true if question is in database
        """
        valid_question = True
        valid_question = self.data.get('question_pool', False)
        valid_question = self.data['question_pool'].get(dimension, False)
        valid_question = self.data['question_pool'][dimension].get(level, False)
        valid_question = self.data['question_pool'][dimension][level].get(question_id, False)
        return valid_question

    def get_valid_roles(self):
        """
        get a list of roles you can use
        """
        return self.data['role_ids']

    def get_valid_projects(self):
        """
        get a list of projects you can use
        """
        return self.data['project_ids']

    def get_number_of_questions_by_dimension(self, levelinput, dimensioninput):
        """
        used for grading percentage at the end of the survey

        retruns a list of each section and the number of questions within
        """
        nodata = None
        for dimension, dimdata in self.data['question_pool'].items():
            for level, questions in dimdata.items():
                for question_id, question in questions.items():
                    if (level == levelinput) and (dimension == dimensioninput):
                        return len(questions)
        return nodata

    def get_active_surveys(self):
        """
        get a list of only active surveys
        """
        active_surveys = []
        for id, values in self.data['survey_ids'].items():
            if values.get('active', False):
                active_surveys.append((id, values['name']))
        return active_surveys

    def get_valid_surveys(self):
        """
        get a list of surveys you can specify
        """
        valid_surveys = {}
        for id, values in self.data['survey_ids'].items():
            valid_surveys[id] = values['name']
        return valid_surveys

    def get_survey_name_by_id(self, survey_id_input):
        """
        gets a survey id by a provided name
        """
        no_survey = None
        for survey_id, values in self.data['survey_ids'].items():
            if survey_id == survey_id_input:
                return values['name']
        return no_survey

    def get_project_id_by_name(self, project_name):
        """
        gets a project id by a provided name
        """
        no_project = None
        for project_id, value in self.data['project_ids'].items():
            if value == project_name:
                return project_id
        return no_project
class HomePageForm(FlaskForm):
    """
    main index form to start a new survey
    """
    username = StringField('What is your username?', validators=[DataRequired()])

    jobrole_choicelist = []
    project_choicelist = []
    survey_choicelist = []
    dao = JsonDb()
    for k, v in dao.get_valid_roles().items():
        jobrole_choicelist.append((k, v))
    print(dao.get_active_surveys())
    for k, v in dao.get_valid_projects().items():
        project_choicelist.append((k, v))
    for k, v in dao.get_active_surveys():
        survey_choicelist.append((k, v))

    jobrole = SelectField('What is your relation to the project?', choices=jobrole_choicelist)
    #[('1', 'ops'), ('2', 'qa'), ('3', 'developer'), ('4', 'dev manager'), ('5', 'product owner'), ('6', 'architect'), ('7', 'director'), ('8', 'support')])
    survey = SelectField('Select an open survey', choices=survey_choicelist)
    project = SelectField('Select a project', choices=project_choicelist)
    #[('1', 'crm'), ('py', 'Python'), ('text', 'Plain Text')])
    submit = SubmitField('Start the survey!')

class SurveyForm(FlaskForm):
    """
    a metaclass template (the royal we) to generate the survey from
    we overload the questions dynamically inside function generate_survey_questions()
    we retrieve the hidden input fields below as request arguements from the homepage
    """
    project_name = HiddenField("project_name")
    survey_name = HiddenField("survey_name")
    jobrole_name = HiddenField("jobrole_name")
    project_id = HiddenField("project_id")
    survey_id = HiddenField("survey_id")
    jobrole_id = HiddenField("jobrole_id")
    username = HiddenField("username")

def generate_survey_questions():
    """
    you must run this function before starting the app, it makes lots of classes/forms.

    dynamically generate JSON test questions into WTF form classes with field properties
    heading_class_name is cast into a class with each level containing the questions in dict() elements
    last, a submit button is created
    """
    for dimension in dao.data['question_pool']:
        #print(dimension)
        for level, questions in dao.data['question_pool'][dimension].items():
            #print(level, questions)
            heading_class_name = "{dimension}_level_{level}".format(dimension=dimension, level=level)
            question_form = {}
            for id, question in questions.items():
                #print(question)
                question_form[id] = BooleanField(question)

            setattr(SurveyForm, heading_class_name, FormField(type(heading_class_name, (FlaskForm,), question_form), id="id{}".format(heading_class_name)))


    setattr(SurveyForm, 'biggest_hurdle', TextAreaField("What is your biggest pain point in the realm of operationally maturity?"))
    setattr(SurveyForm, 'submit', SubmitField('Complete Survey'))

# define functions to be used by the routes (just one here)

# retrieve all the names from the dataset and put them into a list
def get_names(source):
    names = []
    for row in source:
        name = row["name"]
        names.append(name)
    return sorted(names)

# all Flask routes below

@app.route('/manage/votes', methods=['GET', 'POST'])
def managevotes():
    pass

@app.route('/manage/jobroles', methods=['GET', 'POST'])
def managejobrole():
    pass

@app.route('/manage/surveys', methods=['GET', 'POST'])
def managesurvey():
    pass

# show the product scoreboard
# http://127.0.0.1:5000/scoreboard?system=crm&survey_id=3
@app.route('/scoreboard', methods=['GET'])
def scoreboard():
    """
    ssS
    """
    return render_template('scoreboard.html')

@app.route('/survey', methods=['GET'])
def survey_get():
    message = ""

    jobrole_id = request.args.get('jobrole_id')
    survey_id = request.args.get('survey_id')
    project_id = request.args.get('project_id')
    username = request.args.get('username').title()

    conn = sqlite3.connect("db.sqlite")
    qao = conn.cursor()
    sdb = SqliteDb()
    already_voted = False
    for row in sdb.does_user_exist_in_survey(qao, username, survey_id):
        already_voted = True
    if already_voted:
        message = "You already voted!"
        return render_template('votedalready.html', message=message, survey_id=survey_id, survey_name=survey_id, username=username, jobrole_name=jobrole_id, project_name=project_id)


    try:
        jobrole_name = dao.get_valid_roles()[jobrole_id].title()
    except KeyError:
        return "Malformed input error. That isn't a valid jobrole.", 400
    try:
        survey_name = dao.get_valid_surveys()[survey_id]
    except KeyError:
        return "Malformed input error. That isn't a valid survey.", 400
    try:
        project_name = dao.get_valid_projects()[project_id]
    except KeyError:
        return "Malformed input error. That isn't a valid project.", 400
    project_name = project_name.title()
    form = SurveyForm(jobrole_id=jobrole_id, survey_id=survey_id, project_id=project_id, jobrole_name=jobrole_name, survey_name=survey_name, project_name=project_name, username=username)

    return render_template('survey.html', jobrole_id=jobrole_id, survey_id=survey_id, project_id=project_id, survey_name=survey_name, jobrole_name=jobrole_name, project_name=project_name, username=username, form=form, message=message)

def get_question_levels(form):
    """
    extracts a list of levels from the form object
    """
    levels = []
    for level in form:
        if "_level_" in level.name:
            if not level.name.endswith("csrf_token"):
                levels.append(level.name)
    return levels

def get_questions(form, level):
    """
    retrieve a list of questions from the sub form inside a dimension
    """
    questions = []
    for question in form[level].form:
        if not question.name.endswith("csrf_token"):
            questions.append(question.name)
    return questions

@app.route('/survey/submitted', methods=['POST'])
def survey_post():
    tuuid = "voterid_{}".format("".join(str(uuid.uuid4()).split("-")[1:]))
    conn = sqlite3.connect("db.sqlite")
    qao = conn.cursor()
    form = SurveyForm()
    if form.validate_on_submit():
        username = form['username'].data
        jobrole_name = form['jobrole_name'].data
        survey_name = form['survey_name'].data
        project_name = form['project_name'].data
        jobrole_id = form['jobrole_id'].data
        survey_id = form['survey_id'].data

        project_id = form['project_id'].data
        message = "{}, your answers were recorded for {}.".format(username.title(), project_name.lower())

        qao.execute("INSERT INTO voter_registry VALUES (?,?,?,?,?,?)", (tuuid, survey_id, project_id, username, datetime.datetime.now(), jobrole_id))
        questions_answered_true = {}
        for level in get_question_levels(form):
            dimension = level.split("_level_")[0]
            questions_answered_true[level] = {}
            level_number = level.split("level_")[1]
            questions = get_questions(form, level)
            for question_id in questions:
                question_id = "".join(question_id.split("-")[1:])
                vote_value = form[level].form[question_id].data
                if dao.validate_question(dimension, level_number, question_id):
                    #print("{} == {}".format(question_id, vote_value))
                    if vote_value == True:
                        questions_answered_true[level][question_id] = True
                    qao.execute("INSERT INTO vote VALUES (?,?,?)", (tuuid, question_id, vote_value))
                else:
                    print("Invalid form value provided {}".format(question_id))
        conn.commit()
        for dimension_level, votes in questions_answered_true.items():
            dimension = dimension_level.split("_level_")[0]
            level_number = dimension_level.split("level_")[1]
            question_count_total = dao.get_number_of_questions_by_dimension(level_number, dimension)
            percentage = int((len(votes)/question_count_total) * 100)
            print("{} for {} - {}_level_{} scored as {}%".format(username, project_name, dimension, level_number, percentage))
            qao.execute("INSERT INTO vote_matrix_achievement VALUES (?,?,?,?)", (tuuid, dimension, level_number, percentage))
            conn.commit()
        return render_template('voted.html', form=form, message=message, survey_id=survey_id, survey_name=survey_name, username=username, jobrole_name=jobrole_name, project_name=project_name)

@app.route('/summary/detail/<survey_id>', methods=['GET'])
def summary_detail(survey_id):
    conn = sqlite3.connect("db.sqlite")
    qao = conn.cursor()
    survey_name = dao.get_survey_name_by_id(survey_id)

    avg_scores = {"crm_project": { "operability": {"avg": 1, "max": 1, "min": 0}}}
    ind_scores = {"crm_frontend": { "jkelley": { "date": "datetime", "title": "developer", "scores": { "level 1": { "operability": "100", "availability": "50"}, "level 2": { "operability": "100", "availability": "50"}}}}}
    ind_answers = {"crm_project": { "jkelley": { "date": "datetime", "title": "developer", "answers": { "level 1": { "383838838388383": True}}}}}

    # used by template
    ind_scores_real = {}
    avg_scores_real = {}


    # create dict of votes
    votes = qao.execute("SELECT * FROM vote")
    votes_d = {}
    for vote in votes:
        uuid = vote[0]
        question_id = vote[1]
        answer = vote[2]
        votes_d[uuid] = {question_id: answer}

    # create dict of achievements
    achivements = qao.execute("SELECT * FROM vote_matrix_achievement")
    achievements_d = {}
    for achivement in achivements:
        uuid = achivement[0]
        dimension_text = achivement[1]
        dimension_level = achivement[2]
        percent = achivement[3]
        achievements_d[uuid] = {"text": dimension_text, "level": dimension_level, "percent": percent}

    # process votes
    for project_name in dao.get_valid_projects().values():
        ind_scores_real[project_name] = {}
        avg_scores_real[project_name] = {}
    for project_name in dao.get_valid_projects().values():
        project_id = dao.get_project_id_by_name(project_name)
        print(project_name, project_id, survey_id)
        query = qao.execute("SELECT * FROM voter_registry")
        for col in query:
            col_uuid = col[0]
            col_survey_id = col[1]
            col_project_id = col[2]
            col_username = col[3]
            col_datetime = col[4]
            col_role_id = col[5]

            if (survey_id == col_survey_id and project_id == col_project_id):
                print(col)
                ind_scores_real[project_name][col_username] = {"username": col_username, "date": col_datetime, "title": col_role_id, "scores": {}}

    print(ind_scores_real)
    return render_template('summarydetail.html', valid_projects=dao.get_valid_projects().values(), ind_scores=ind_scores_real, avg_scores=avg_scores, survey_name=survey_name)

# index
@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    form = HomePageForm()
    message = ""
    if form.validate_on_submit():
        username = form.username.data
        jobrole_id = form.jobrole.data
        survey_id = form.survey.data
        project_id = form.project.data

        roleids = [x for x in dao.get_valid_roles().keys()]
        projectids = [x for x in dao.get_valid_projects().keys()]

        if jobrole_id in roleids:
            message += "" + dao.get_valid_roles()[jobrole_id] + " is your job title..."
        if project_id in projectids:
            message += "" + dao.get_valid_projects()[project_id] + " is your project..."

        return redirect("/survey?jobrole_id={}&survey_id={}&project_id={}&username={}".format(jobrole_id, survey_id, project_id, username), code=302)
        # empty the form field
        form.username.data = ""
        form.jobrole.data = ""
        form.survey.data = ""
        form.project.data = ""

    surveys = dao.get_valid_surveys()
    return render_template('index.html', form=form, message=message, orgname=dao.get_orgname(), allsurveys=surveys)

def select(verbose=True):
    sql = "SELECT * FROM vote"
    recs = qao.execute(sql)
    if verbose:
        for row in recs:
            print(row)

    sql = "SELECT * FROM voter_registry"
    recs = qao.execute(sql)
    if verbose:
        for row in recs:
            print(row)

    sql = "SELECT * FROM vote_matrix_achievement"
    recs = qao.execute(sql)
    if verbose:
        for row in recs:
            print(row)


# keep this as is
if __name__ == '__main__':
    dao = JsonDb()

    conn = sqlite3.connect("db.sqlite")
    qao = conn.cursor()

    # generate me schema
    qao.execute('''CREATE TABLE IF NOT EXISTS voter_registry
                 (uuid_xref text, survey_id text, project_id text, username text, date_iso8601 text, jobrole_id text)''')

    qao.execute('''CREATE TABLE IF NOT EXISTS vote
                 (uuid_xref text, question_id text, answer integer)''')

    qao.execute('''CREATE TABLE IF NOT EXISTS vote_matrix_achievement
                 (uuid_xref text, dimension text, level text, percent integer)''')

    select()
    conn.commit()

    generate_survey_questions()
    app.run(debug=True, port=9999)
