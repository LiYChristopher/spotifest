# Frontend helpers
from flask.ext.wtf import Form
from wtforms import (StringField, SubmitField, SelectField,
                    validators)
from wtforms.fields.html5 import DecimalRangeField
from wtforms.widgets import Select
from db import get_parameters


class SearchForm(Form):
    '''Form for Echonest search on festival page.'''
    artist_search = StringField("artist_search",
                                validators=[validators.DataRequired()])

    submit_search = SubmitField("Search")


class ArtistSelect(Form):
    '''Select an artist fetched from search form query.'''
    artist_display = SelectField('artist_options', coerce=int,
                                 option_widget=Select(multiple=False))
    confirm_select = SubmitField("Add")


class ParamsForm(Form):
    '''Form for festival page, interactive 
    Echonest parameters.'''
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


def populate_params(params_form, saved_params):
    '''Load saved parameters from dB.'''
    if saved_params:
        params_form.danceability.value = saved_params[0]
        params_form.hotttnesss.value = saved_params[1]       
        params_form.energy.value = saved_params[2]
        params_form.variety.value = saved_params[3]
        params_form.adventurousness.value = saved_params[4]


class SuggestedPlaylistButton(Form):
    add_button = SubmitField("Add the Spotifest team's favorites!")
    confirm_button = SubmitField("Accept our suggestions?")
