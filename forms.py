from wtforms import Form, TextAreaField, validators

class PoemSubmissionForm(Form):
	poem = TextAreaField('Poem text', [validators.Required()])