from flask_wtf import Form
from wtforms import StringField, SubmitField,RadioField  ,SelectField, TextAreaField,IntegerField,FloatField
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

class CustomerSegmentForm(Form):
    project_title = StringField('Title', validators=[DataRequired(), Length(min=5)])
    project_desc = TextAreaField('Project Description', validators=[DataRequired()],render_kw={"placeholder": "Project Description","rows": "5", "cols": "80"})
    file_regex = TextAreaField('File regex Pattern',validators=[DataRequired(), Length(min=5)],render_kw={"placeholder": "FileName Regex Pattern","rows": "10", "cols": "80"})
    def validate_file_regex(form, field):
        try:
            (re.compile(field.data))
        except re.error:
            raise ValidationError('Please provide valid regex pattern.')

    column_schema = TextAreaField('Columns Schema', validators=[DataRequired()],render_kw={"placeholder": "Columns Schema(Json Format)","rows": "10", "cols": "81"})
    def validate_train_schema(form, field):
        try:
            x = ((json.loads(str(field.data).replace("\'", "\""))))
        except Exception as e:
            print('Please provide valid columns schemaa(json format)')
            raise ValidationError('Please provide valid columns schema(json format)')
    cloud = SelectField('Cloud',choices = [('AWS','AWS'),('GCP','GCP')])
    profit_margin = IntegerField("Profit Margin",render_kw={"placeholder": "Profit margin"})
    discount_cash_flow_rate = IntegerField("discounted cash flow rate",render_kw={"placeholder": "Discounted Cash Flow Rate"})
    submit = SubmitField('Add Project',)
