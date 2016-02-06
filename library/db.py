import base64
import datetime
from library.app import app, mysql, celery


@celery.task(name='save_festival')
def save_to_database(festivalName, userId, playlistId, playlistURL, catalogId, urlSlug):
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
        cursor.execute("INSERT INTO sessions (festivalName, userId, playlistId, playlistURL, catalogId, urlSlug) VALUES (%s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        print 'saved to database'
    return


@celery.task(name='update_festival')
def update_festival(festivalName, playlistId, playlistURL, urlSlug):
    values = (festivalName, playlistId, playlistURL, urlSlug)
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE sessions SET festivalName=%s, playlistId=%s, playlistURL=%s WHERE urlSlug=%s",
                        (festivalName, playlistId, playlistURL, urlSlug))
        connection.commit()
        print 'saved to database'
    return


def save_contributor(festivalId, userId, ready=0, hotness=None, 
                    danceability=None, energy=None, variety=None, advent=None,
                    organizer=0):
    festivalId = int(festivalId)
    userId = str(userId)
    values = (festivalId, userId, ready, hotness, 
                danceability, energy, variety, advent, organizer)
    print ("Saving contributor {} to festival {}".format(userId, festivalId))
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO contributors VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        print 'saved to database'
    return

def get_contributors(festivalId):
    '''
    return a list with all the contributors id of
    the festival
    '''
    print type(festivalId)
    print (festivalId)
    connection = mysql.get_db()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT userId FROM contributors WHERE (festivalId = %s AND organizer = 1)", (festivalId,))
    except:
        print ("Database can't be reached")
        return None
    data1 = cursor.fetchall()
    if data1:
        all_users = [user[0].encode('utf-8') for user in data1]
    else:
        print ("There is no organizer assigned.")
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT userId FROM contributors WHERE (festivalId = %s AND organizer = 0)", (festivalId,))
        data2 = cursor.fetchall()
    except:
        print ("Database can't be reached..")
        return None
    if data2:
        contributors = [user[0].encode('utf-8') for user in data2]
        all_users.append(contributors)
        
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
        try:
             cursor.execute("SELECT * FROM sessions WHERE urlSlug = %s", (urlSlug,))
             data = cursor.fetchall()
        except:
            return None
        print 'DATA', data
        festivalId = int(data[0][0])
        festivalName = str(data[0][1])
        userId = str(data[0][2])
        playlistId = str(data[0][3])
        playlistURL = str(data[0][4])
        catalogId = str(data[0][5])
        values = [festivalId, festivalName, userId, playlistId, playlistURL, catalogId]
        return values


'''
def get_info_from_database(urlSlug):

    return a list with all the information from the
    database for a certain festival id

    print ("THE URL SLUG {}".format(urlSlug))
    connection = mysql.connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sessions WHERE urlSlug = %s", (urlSlug,))
        data = cursor.fetchall()
    except:
        return None
    print 'DATA', data
    festivalId = int(data[0][0])
    festivalName = str(data[0][1])
    userId = str(data[0][2])
    playlistId = str(data[0][3])
    playlistURL = str(data[0][4])
    catalogId = str(data[0][5])
    values = [festivalId, userId, playlistId, playlistURL, catalogId]
    return values
'''