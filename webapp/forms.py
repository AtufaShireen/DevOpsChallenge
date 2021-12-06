from flask_wtf import Form
from wtforms import StringField, SubmitField,RadioField  ,SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

import re,json
from wtforms.validators import ValidationError

class ProjectConfigForm(Form):
    project_title = StringField('Title', validators=[DataRequired(), Length(min=5)])
    project_desc = TextAreaField('Project Description', validators=[DataRequired()],render_kw={"placeholder": "Project Description","rows": "5", "cols": "80"})
    file_regex = TextAreaField('File regex Pattern',validators=[DataRequired(), Length(min=5)],render_kw={"placeholder": "FileName Regex Pattern","rows": "10", "cols": "80"})
    def validate_file_regex(form, field):
        try:
            (re.compile(field.data))
        except re.error:
            raise ValidationError('Please provide valid regex pattern.')

    train_schema = TextAreaField('Training Schema', validators=[DataRequired()],render_kw={"placeholder": "Train Schema(Json Format)","rows": "10", "cols": "81"})
    def validate_train_schema(form, field):
        try:
            x = ((json.loads(str(field.data).replace("\'", "\""))))
        except Exception as e:
            print('Please provide valid trina schemaa(json format)')
            raise ValidationError('Please provide valid training schema(json format)')
    test_schema = TextAreaField('Testing Schema', validators=[DataRequired()],render_kw={"placeholder": "Predict Schema(Json Format)","rows": "10", "cols": "81"})
    def validate_test_schema(form, field):
        try:
            x = ((json.loads(str(field.data).replace("\'", "\""))))
        except Exception as e:
            print('Please provide valid testing schemaa(json format)')
            raise ValidationError('Please provide valid testing schemaa(json format)')
    mltype = RadioField('Problem Type',choices = [('classification','classification'),('regression','regression')])
    cloud = SelectField('Cloud',choices = [('AWS','AWS'),('GCP','GCP')])
    submit = SubmitField('Add Project')

{'id':'int','ft_1':'int','ft2':'int'}