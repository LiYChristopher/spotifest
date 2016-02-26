# Spotifest

## Background

Spotifest was submitted as a project by Chris Li, Tycho van Kleef and Andres Hazard for Rmotr.com's Demo Day.
The basic requirements of the project was that it had to derive functionality from a large enterprise API. We wanted
to work with music, specifically in regards to how we can discover music more rapidly and get friends involved in the
process. So we decided to use the Spotify and Echonest APIs to create a music festival playlist generator, that would 
algorithmically produce unique playlists based on a user(s)' listening preferences on Spotify. 

- Whenever a user creates a "festival", they're creating a staging area where listening preferences, in the form of artists, of the organizer of the
festival as well as contributors (people who join the festival through a unique password) are stored. 
- In addition we're also keeping track of a set of parameters that control fine-tuned metrics developed by Echonest, which dictates the overall
feel of the playlist. 
- When all users are ready, 50 song playlists will be generated from all the data - preferences, parameter inputs - bound 
to a particular festival.

Currently this project is still maintained by the entire original team, and we will continue to improve or add new features
over time.