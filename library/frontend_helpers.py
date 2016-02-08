# Frontend helpers
from flask_wtf import Form
from wtforms import (StringField, SubmitField, SelectField,
                    validators)
from wtforms.fields.html5 import DecimalRangeField
from wtforms.widgets import Select


class SearchForm(Form):
    artist_search = StringField('search_artist',
                                validators=[validators.DataRequired()])
    submit = SubmitField("Search")


class ArtistSelect(Form):
    artist_display = SelectField('artist_options', coerce=int,
                                 option_widget=Select(multiple=False))
    confirm_button = SubmitField("Add!")


class ParamsForm(Form):
    name = StringField('name', [validators.DataRequired()],
                       default='Festify 2016')
    danceability = DecimalRangeField('danceability',
                                     [validators.NumberRange(min=0, max=1)],
                                     default=0.5)
    hotttnesss = DecimalRangeField('hotttnesss',
                                   [validators.NumberRange(min=0, max=1)],
                                   default=0.5)
    energy = DecimalRangeField('energy',
                               [validators.NumberRange(min=0, max=1)],
                               default=0.5)
    variety = DecimalRangeField('variety',
                                [validators.NumberRange(min=0, max=1)],
                                default=0.5)
    adventurousness = DecimalRangeField('adventurousness',
                                        [validators.NumberRange(min=0, max=1)],
                                        default=0.5)
    ready_butt = SubmitField("Propose Vision")
    unready_butt = SubmitField("Change Vision")


class SuggestedPlaylistButton(Form):
    add_button = SubmitField("Add the Festify team's favorites!")
    confirm_button = SubmitField("Accept our suggestions?")
