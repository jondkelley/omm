# using python 3
from flask import Flask, render_template, make_response, request, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FormField, BooleanField, SelectField
from wtforms.validators import Required
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
Bootstrap(app) # Flask-Bootstrap requires this line
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# with Flask-WTF, each web form is represented by a class
# "NameForm" can change; "(FlaskForm)" cannot
# see the route for "/" and "index.html" to see how this is used

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
        valid_surveys = []
        for id, values in self.data['survey_ids'].items():
            valid_surveys.append((id, values['name']))
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
        pass

class StartForm(FlaskForm):
    username = StringField('What is your username?', validators=[Required()])

    jobrole_choicelist = []
    project_choicelist = []
    survey_choicelist = []
    dbo = JsonDb()
    for k, v in dbo.get_valid_roles().items():
        jobrole_choicelist.append((k, v))
    print(dbo.get_active_surveys())
    for k, v in dbo.get_valid_projects().items():
        project_choicelist.append((k, v))
    for k, v in dbo.get_active_surveys():
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
    pass

def generate_survey_questions():
    """
    you must run this function before starting the app, it makes lots of classes/forms.

    dynamically generate JSON test questions into WTF form classes with field properties
    heading_class_name is cast into a class with each level containing the questions in dict() elements
    last, a submit button is created
    """
    for dimension in dbo.data['question_pool']:
        #print(dimension)
        for level, questions in dbo.data['question_pool'][dimension].items():
            #print(level, questions)
            heading_class_name = "{dimension}_level_{level}".format(dimension=dimension, level=level)
            question_form = {}
            for id, question in questions.items():
                #print(question)
                question_form[id] = BooleanField(question)

            setattr(SurveyForm, heading_class_name, FormField(type(heading_class_name, (FlaskForm,), question_form), id="id{}".format(heading_class_name)))
    setattr(SurveyForm, 'submit', SubmitField('Submit Data to Survey'))

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

# operability
@app.route('/take_survey', methods=['GET', 'POST'])
def operability():
    form = SurveyForm()

    # if form1.submit1.data and form1.validate():
    #     pass
    # if form2.submit2.data and form2.validate():
    #     pass
    message = ""

    jobrole_id = request.args.get('jobrole_id')
    survey_id = request.args.get('survey_id')
    project_id = request.args.get('project_id')
    username = request.args.get('username')
    return render_template('survey.html', username=username, form=form, message=message)

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

        roleids = [x for x in dbo.get_valid_roles().keys()]
        projectids = [x for x in dbo.get_valid_projects().keys()]

        if jobrole_id in roleids:
            message += "" + dbo.get_valid_roles()[jobrole_id] + " is your job title..."
        if project_id in projectids:
            message += "" + dbo.get_valid_projects()[project_id] + " is your project..."

        return redirect("/take_survey?jobrole_id={}&survey_id={}&project_id={}&username={}".format(jobrole_id, survey_id, project_id, username), code=307)
        # empty the form field
        form.username.data = ""
        form.jobrole.data = ""
        form.survey.data = ""
        form.project.data = ""

        #res = make_response(render_template('survey.html', form=survey_form, surveyname=form.survey.data, message=message, orgname=dbo.get_orgname(), allsurveys=dbo.get_valid_surveys()))
        # res.set_cookie("whoami", value="{}|{}|{}".format(form.username.data, form.jobrole.data, form.jobrole.data))
        #
        # message += "Cookie set.".format(form.jobrole.data)

    # notice that we don't need to pass name or names to the template

    return render_template('index.html', form=form, message=message, orgname=dbo.get_orgname(), allsurveys=dbo.get_valid_surveys())

# keep this as is
if __name__ == '__main__':
    dbo = JsonDb()
    generate_survey_questions()
    app.run(debug=True)
