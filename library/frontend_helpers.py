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
    name = StringField('Name', [validators.DataRequired()],
                       default='Spotifest 2016')
    danceability = DecimalRangeField('Danceability',
                                     [validators.NumberRange(min=0, max=1)],
                                     default=0.5)
    hotttnesss = DecimalRangeField('Hotttnesss',
                                   [validators.NumberRange(min=0, max=1)],
                                   default=0.5)
    energy = DecimalRangeField('Energy',
                               [validators.NumberRange(min=0, max=1)],
                               default=0.5)
    variety = DecimalRangeField('Variety',
                                [validators.NumberRange(min=0, max=1)],
                                default=0.5)
    adventurousness = DecimalRangeField('Adventurousness',
                                        [validators.NumberRange(min=0, max=1)],
                                        default=0.5)
    ready_butt = SubmitField("Propose Vision")
    unready_butt = SubmitField("Change Vision")


class SuggestedPlaylistButton(Form):
    add_button = SubmitField("Add the Spotifest team's favorites!")
    confirm_button = SubmitField("Accept our suggestions?")
