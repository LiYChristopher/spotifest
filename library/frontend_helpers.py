#Frontend helpers
from flask_wtf import Form
from wtforms import StringField, SubmitField, SelectField, validators
from wtforms.widgets import Select
from pyechonest import artist
from pyechonest import config

config.ECHO_NEST_API_KEY = "SNRNTTK9UXTWYCMBH"

class SearchForm(Form):
    artist_search = StringField('search_artist',
                                validators=[validators.DataRequired()])
    submit = SubmitField("Search")


class ArtistSelect(Form):
    artist_display = SelectField('artist_options', coerce=int,
                                option_widget=Select(multiple=False))
    confirm_button = SubmitField("Add!")

class SuggestedPlaylistButton(Form):
    add_button = SubmitField("Add the Festify team's favorites!")
    confirm_button = SubmitField("Accept our suggestions?")