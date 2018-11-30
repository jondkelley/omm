# using python 3
from flask import Flask, render_template, make_response, request, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FormField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired
import json

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

    def get_questions(self):
        """
        retrieve the question pool
        """
        pass

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

    def start_new_survey(self):
        """
        starts a new survey and marks it active (deactives others)
        """
        pass

    def get_vote_average(self, survey):
        """
        gets the average vote for a service from the summary screen
        """
        dstruct = {"operability": {"maxlevel": "1", "votes": [] }}
        pass

    def votes_detail(self, survey):
        """
        get a list of detailed vote data
        """
        dstruct = {"operability": {"maxlevel": "1", "votes": [] }}
        pass

    def check_if_already_voted(self, username, project):
        """
        returns true if a user already voted in a project
        """
        return ""

    def cast_vote(self, data):
        """
        writes a new vote to disk
        """
        input_contract = {"project_id": { "survey_id": "-1", "username": "nobody", "role_id": "-1", "date": "-1", "votes": {}}}
        # output_structr = {
        # 	"project_id_1": [{
        # 		"survey_id": "1",
        # 		"username": "jkelley",
        # 		"role_id": "1",
        # 		"votes": {
        # 			"00000000050": true
        # 		},
        # 		"achievements": ["Architectual_Operability_Level_3"],
        # 		"date": "393764732923"
        # 	}]}
        value = input_contract.values()[0]
        project_id = input_contract.keys()[0]
        project_id = value['project_id']
        survey_id = value['survey_id']
        username = value['username']
        role_id = value['role_id']
        date = value['date']
        votes = value['votes']

        result = dict()
        project_id_name = "project_id_{}".format(project_id)
        result[project_id_name] = list()
        result[project_id_name].append({"username": username, "survey_id": survey_id, "role_id": role_id, "date": date, "votes": votes})

        pass

class StartForm(FlaskForm):
    username = StringField('What is your name/nickname/alias/psuedonym?', validators=[DataRequired()])

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

    jobrole = SelectField('What is your job role?', choices=jobrole_choicelist)
    #[('1', 'ops'), ('2', 'qa'), ('3', 'developer'), ('4', 'dev manager'), ('5', 'product owner'), ('6', 'architect'), ('7', 'director'), ('8', 'support')])
    survey = SelectField('Select an open survey', choices=survey_choicelist)
    project = SelectField('Select a project', choices=project_choicelist)
    #[('1', 'crm'), ('py', 'Python'), ('text', 'Plain Text')])
    submit = SubmitField('Start the survey!')

class SurveyForm(FlaskForm):
    """
    a metaclass template (the royal we) for questions added dynamically by generate_test_questions()
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
    form = SurveyForm()
    if form.validate_on_submit():
        print("WTF")
        username = form['username'].data
        jobrole_name = form['jobrole_name'].data
        survey_name = form['survey_name'].data
        project_name = form['project_name'].data
        jobrole_id = form['jobrole_id'].data
        survey_id = form['survey_id'].data
        project_id = form['project_id'].data
        print(project_name, survey_name, jobrole_name, username)
        print(dir(form['L/A/M/A_level_1'].form.data))
        message = "{}, your answers were recorded for {}.".format(username.title(), project_name.lower())
        print(form['architectual_operability_level_1'].form['3C0726BE.C643B3E9891E'].data)

        for level in get_question_levels(form):
            dimension = level.split("_level_")[0]
            level_number = level.split("level_")[1]
            questions = get_questions(form, level)
            for question_id in questions:
                question_id = "".join(question_id.split("-")[1:])
                vote_value = form[level].form[question_id].data
                #print(question_id)
                if dao.validate_question(dimension, level_number, question_id):
                    print("{} == {}".format(question_id, vote_value))
                else:
                    print("Invalid form value provided {}".format(question_id))
                #print(form[level].form.data[question].form.data)
                pass#print(question, form[level].form[question].data)

        return render_template('voted.html', form=form, message=message, survey_id=survey_id, survey_name=survey_name, username=username, jobrole_name=jobrole_name, project_name=project_name)

# index
@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    names = ['crm', 'wp']#get_names(ACTORS)
    # you must tell the variable 'form' what you named the class, above
    # 'form' is the variable name used in this template: index.html
    form = StartForm()
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

        #res = make_response(render_template('survey.html', form=survey_form, surveyname=form.survey.data, message=message, orgname=dao.get_orgname(), allsurveys=dao.get_valid_surveys()))
        # res.set_cookie("whoami", value="{}|{}|{}".format(form.username.data, form.jobrole.data, form.jobrole.data))
        #
        # message += "Cookie set.".format(form.jobrole.data)

    # notice that we don't need to pass name or names to the template
    surveys = dao.get_valid_surveys()
    return render_template('index.html', form=form, message=message, orgname=dao.get_orgname(), allsurveys=surveys)

# keep this as is
if __name__ == '__main__':
    dao = JsonDb()
    generate_survey_questions()
    app.run(debug=True, port=9999)
