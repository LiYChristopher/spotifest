import base64
import datetime
from library.app import app, mysql, celery


@celery.task(name='save_festival')
def save_to_database(festivalName, userId, playlistId,
                     playlistURL, catalogId, urlSlug):
    '''
    saves infromation the data base.
    festivalId will be created automatically
    '''
    festivalName = str(festivalName)
    userId = str(userId)
    playlistId = str(playlistId)
    playlistURL = str(playlistURL)
    catalogId = str(catalogId)
    values = (festivalName, userId, playlistId, playlistURL, catalogId, urlSlug)
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO sessions (festivalName, userId, playlistId, playlistURL, catalogId, urlSlug)\
                        VALUES (%s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        print 'saved to database'
    return


@celery.task(name='update_festival')
def update_festival(festivalName, playlistId, playlistURL, urlSlug):
    values = (festivalName, playlistId, playlistURL, urlSlug)
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE sessions SET festivalName=%s, playlistId=%s,\
                        playlistURL=%s WHERE urlSlug=%s",
                        (festivalName, playlistId, playlistURL, urlSlug))
        connection.commit()
        print 'saved to database'
    return


def save_contributor(festivalId, userId, ready=0, hotness=None,
                     danceability=None, energy=None, variety=None, advent=None,
                     organizer=0):
    '''
    requires festivalId and userId,
    saves whatever else you also put in it in the contributor table
    '''
    festivalId = int(festivalId)
    userId = str(userId)
    values = (festivalId, userId, ready, hotness,
              danceability, energy, variety, advent, organizer)
    print ("Saving contributor {} to festival {}".format(userId, festivalId))
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO contributors VALUES\
                       (%s, %s, %s, %s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        print 'saved to database'
    return

def get_contributors(festivalId):
    '''
    return a list with all the contributors id of
    the festival. THE FIRST contributor == organizer
    '''
    print type(festivalId)
    print (festivalId)
    connection = mysql.get_db()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM contributors WHERE\
                       (festivalId = %s AND organizer = 1)", (festivalId,))
    except:
        print ("Database can't be reached")
        return None
    d1 = cursor.fetchall()
    if d1:
        all_users = {'owner': {'userId': str(d1[0][1]), 'ready': int(d1[0][2]), 
                                'hotness': float(d1[0][3]), 'danceability': float(d1[0][4]),
                                'energy': float(d1[0][5]), 'variety': float(d1[0][6]),
                                'variety': float(d1[0][7]), 'adventurousness': float(d1[0][8])}}
    else:
        print ("There is no organizer assigned.")
        return None

    try:
        connection = mysql.get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT userId FROM contributors WHERE\
                       (festivalId = %s AND organizer = 0)", (festivalId,))
        d2 = cursor.fetchall()
        print ("contributors: {}".format(d2))
    except:
        print ("Database can't be reached..")
        return None
    if d2:
        contributors = {{str(u[0][1]): {'ready': int(u[0][2]), 
                        'hotness': float(u[0][3]), 
                        'danceability': float(u[0][4]),
                        'energy': float(u[0][5]), 
                        'variety': float(u[0][6]),
                        'variety': float(u[0][7]), 
                        'adventurousness': float(u[0][8])}} for u in d2}
        all_ready = 1
        for contributor in contributors:
            if contributor['ready'] == 0:
                all_ready = 0
                break

        all_users.update({'contributors': contributors, 'all_ready': all_ready})

    print ('contributors retrieved from database: {}'.format(all_users))
    return all_users


def get_info_from_database(urlSlug):
    '''
    return a list with all the information from the
    database for a certain festival id
    '''
    print "URL SLUG IS {}".format(urlSlug)
    with app.app_context():
        connection = mysql.get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE urlSlug = %s", (urlSlug,))
        data = cursor.fetchall()
        if not data:
            return None
        print 'DATA', data
        festivalId = int(data[0][0])
        festivalName = str(data[0][1])
        userId = str(data[0][2])
        playlistId = str(data[0][3])
        playlistURL = str(data[0][4])
        catalogId = str(data[0][5])
        values = [festivalId, festivalName, userId,
                  playlistId, playlistURL, catalogId]
        return values
