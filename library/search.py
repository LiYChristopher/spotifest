#search.py

from flask import render_template, request, redirect, url_for, session, g

from library.app import app
from frontend_helpers import SearchForm, SuggestedPlaylistButton, ArtistSelect
from helpers import search_artist_echonest

class User():
    artists = ['a', 'b']
    search_results = 0

User()

@app.route('/search', methods=('GET', 'POST'))
def search(s_results=None):
    searchform = SearchForm()
    suggest_pl_but = SuggestedPlaylistButton()
    art_select = ArtistSelect(request.form)

    if searchform.validate_on_submit():
        #if request.form.get('artist_search'):
        new_artist = searchform.artist_search.data
        User.search_results = search_artist_echonest(new_artist)
        art_select.artist_display.choices = User.search_results

    if art_select.artist_display.data:
        if art_select.is_submitted():
            option_n = int(art_select.artist_display.data) + 1
            chosen_art = User.search_results[option_n][1]
            User.artists.append(chosen_art)

    if suggest_pl_but.validate_on_submit():
        if request.form.get('add_button'):
            User.artists.append(["DO 1"])



    return render_template('search.html', searchform=searchform,
                            art_select=art_select,
                            suggest_pl_but=suggest_pl_but,
                            artists=User.artists)





@app.route('/success', methods=('GET', 'POST'))
def good_search(lala=None):
    return render_template('success.html')

