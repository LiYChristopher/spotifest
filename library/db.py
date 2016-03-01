import base64
import datetime
from . import app, mysql, celery
from pyechonest.catalog import Catalog


@celery.task(name='save_festival')
def save_to_database(festivalName, userId, playlistId,
                     playlistURL, catalogId, urlSlug):
    ''' Executes an insert query for festival
    information on sessions table in dB.'''
    festivalName = str(festivalName)
    userId = str(userId)
    playlistId = str(playlistId)
    playlistURL = str(playlistURL)
    catalogId = str(catalogId)
    values = (festivalName, userId, playlistId, playlistURL, catalogId, urlSlug)
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO sessions (festivalName, userId, playlistId,\
                        playlistURL, catalogId, urlSlug)\
                        VALUES (%s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        app.logger.warning("DB -- Festival at '{}'"
                           "saved to database".format(urlSlug))
    return


@celery.task(name='update_festival', ignore_result=True)
def update_festival(festivalName, urlSlug, playlistId=None, playlistURL=None):
    ''' Executes an update query for festival
    information on sessions table in dB.'''
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        if playlistId and playlistURL:
            values = (festivalName, playlistId, playlistURL, urlSlug)
            cursor.execute("UPDATE sessions SET festivalName=%s, playlistId=%s,\
                           playlistURL=%s WHERE urlSlug=%s",
                           (festivalName, playlistId, playlistURL, urlSlug))
        else:
            values = (festivalName, urlSlug)
            cursor.execute("UPDATE sessions SET festivalName=%s, WHERE urlSlug=%s",
                           (festivalName, urlSlug))
        connection.commit()
        app.logger.warning("DB -- values saved to festival '{}'.".format(urlSlug))
    return


def update_parameters(festivalId, userId, hotttnesss, danceability,
                      energy, variety, advent):
    ''' Executes an update query for parameter input 
    on contributors table. 
    '''
    festivalId = int(festivalId)
    userId = str(userId)
    hotttnesss = float(hotttnesss)
    danceability = float(danceability)
    energy = float(energy)
    variety = float(variety)
    advent = float(advent)
    values = (hotttnesss, danceability, energy, variety, advent, festivalId, userId)
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE contributors SET hotness=%s, danceability=%s, energy=%s,\
                        variety=%s, adventurousness=%s, ready=1 WHERE festivalId=%s AND userId=%s", values)
        connection.commit()
        app.logger.warning("DB -- parameter settings updated for "
                           "user '{}' in festival '{}'".format(userId, festivalId))
    return


def get_parameters(user_id, url_slug):
    ''' Executes a select query on contributors table,
    retrieving parameter for user at festival located at url_slug.
    '''
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT c.hotness, c.danceability, c.energy, c.variety,"
            "c.adventurousness FROM contributors as c INNER JOIN sessions as s on "
            "c.festivalId = s.festivalId WHERE (c.userId = '{}' and s.urlSlug = '{}')"
            .format(user_id, url_slug))
        data = cursor.fetchall()
        if not data[0][0]:
            return None

        h = int(data[0][0])
        d = int(data[0][1])
        e = int(data[0][2])
        v = int(data[0][3])
        a = int(data[0][4])

        values = [h, d, e, v, a]
        app.logger.warning("DB - parameters retrieved for"
                           "'{}' at '{}'".format(user_id, url_slug))
        return values


@celery.task(name='save_contributor', ignore_result=True)
def save_contributor(festivalId, userId, ready=0, hotness=None,
                     danceability=None, energy=None, variety=None, advent=None,
                     organizer=0):
    ''' Executes insert query on contributors table for
    new contributor at festival at festivalId
    '''
    festivalId = int(festivalId)
    userId = str(userId)
    values = (festivalId, userId, ready, hotness,
              danceability, energy, variety, advent, organizer)

    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO contributors VALUES\
                       (%s, %s, %s, %s, %s, %s, %s, %s, %s)", values)
        connection.commit()
        app.logger.warning("DB - Saved contributor {} to"
                           "festival {}".format(userId, festivalId))
    return


def get_contributors(festivalId):
    ''' Executes select query on contributors table for
    contributors for festival at festivalId (this includes the owner)
    '''
    connection = mysql.get_db()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM contributors WHERE\
                       (festivalId = %s AND organizer = 1)", (festivalId,))
        _org = cursor.fetchall()
    except:
        app.logger.error("SQL Query failed - check dB schema.")
        return None
    else:
        if not _org[0][0]:
            app.logger.error("DB -- No organizer found"
                             " for festival at'{}'".format(festivalId))
            return None
        all_users = {'organizer': {'userId': str(_org[0][1]),
                                   'ready': int(_org[0][2]),
                                   'hotness': (_org[0][3]),
                                   'danceability': (_org[0][4]),
                                   'energy': (_org[0][5]),
                                   'variety': (_org[0][6]),
                                   'adventurousness': (_org[0][7])}}
    #fetching the contributors
    try: 
        cursor.execute("SELECT * FROM contributors WHERE\
                       (festivalId = %s AND organizer = 0)", (festivalId,))
        _ctbrs = cursor.fetchall()
    except:
        app.logger.error("DB -- No organizer found"
                         " for festival at'{}'".format(festivalId))
        return None
    else:
        if _ctbrs:
            contributors = {str(user[1]): {'ready': int(user[2]),
                                           'hotness': user[3],
                                           'danceability': user[4],
                                           'energy': user[5],
                                           'variety': user[6],
                                           'adventurousness': user[7]} for user in _ctbrs}
            c_names = [c for c in contributors]
            contributors['c_names'] = c_names
            all_ready = 1
            for contributor in contributors['c_names']:
                if contributors[contributor]['ready'] == 0:
                    all_ready = 0
                    app.logger.warning("DB - At least 1 user isn't"
                                       " ready in festival '{}'".format(festivalId))
                    break

            all_users.update({'contributors': contributors, 'all_ready': all_ready})
        app.logger.warning("All users are in "
                           "festival '{}' are '{}'".format(festivalId, all_users))
        return all_users


def get_info_from_database(urlSlug):
    ''' Executes select query on sessions table
    for festival information at urlSlug.
    '''
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE urlSlug = %s", (urlSlug,))
        data = cursor.fetchall()
        if not data:
            return None
        festivalId = int(data[0][0])
        festivalName = str(data[0][1])
        userId = str(data[0][2])
        playlistId = str(data[0][3])
        playlistURL = str(data[0][4])
        catalogId = str(data[0][5])
        values = [festivalId, festivalName, userId,
                  playlistId, playlistURL, catalogId]
        app.logger.warning("Info for festival '{}' retrieved.".format(urlSlug))
        return values

def get_user_festivals(user_id):
    ''' Executes select query on contributors table
    for festival info where user at user_id is a contributor.
    '''
    connection = mysql.get_db()
    cursor = connection.cursor()
    query = ("SELECT c.userId, s.festivalId, s.festivalName, s.urlSlug, "
        "c.organizer FROM sessions as s INNER JOIN contributors as c on "
        "s.festivalId = c.festivalId  where s.festivalId = c.festivalId "
        "and c.userId = '{}'".format(user_id))

    cursor.execute(query)
    d = cursor.fetchall()
    organized_festivals = {u[1]: {'festival_name': u[2], 'url_slug': u[3]}
                           for u in d if u[4] == 1}
    contributed_festivals = {u[1]: {'festival_name': u[2], 'url_slug': u[3], 'user_id': u[0]}
                             for u in d if u[4] == 0}
    app.logger.warning("'{}' organized: '{}'".format(user_id, organized_festivals))
    app.logger.warning("'{}' contributed: '{}'".format(user_id, contributed_festivals))
    user_festivals = {}

    if organized_festivals:
        user_festivals = {'organizer': organized_festivals}
    if contributed_festivals:
        user_festivals.update({'contributor': contributed_festivals})
    app.logger.warning("All festivals involved in: '{}'".format(user_festivals))
    return user_festivals


def get_average_parameters(festivalId):
    ''' Executes average function for all parameter inputs
    associated with a festival at festivalId.
    '''
    with app.app_context():
        connection = mysql.get_db()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT AVG(hotness), AVG(danceability), \
                            AVG(energy), AVG(variety), AVG(adventurousness) \
                            from contributors where festivalId = %s", (festivalId,))
            data = cursor.fetchall()
        except:
            app.logger.error("Error while retrieving averages. Check dB schema.")
            return None
        average_parameters = [float(data[0][0]), float(data[0][1]),
                              float(data[0][2]), float(data[0][3]),
                              float(data[0][4])]
        app.logger.warning("Average Parameters for"
                           "festival '{}': {}".format(festivalId, average_parameters))
        return average_parameters


@celery.task(name='delete_session', ignore_result=True)
def delete_session(urlSlug):
    ''' Celery task that removes festival and catalog object
    from database and API key, respectively.
    '''
    with app.app_context():
        connection = mysql.connect()
        cursor = connection.cursor()
        festival = get_info_from_database(urlSlug)
        if not festival:
            return None
        festival_catalog = Catalog(festival[5])
        festival_catalog.delete()
        cursor.execute("DELETE FROM sessions WHERE urlSlug=%s", (urlSlug,))
        connection.commit()
    return


@celery.task(name='routine_deletion_expired', ignore_result=True)
def delete_expired_session():
    ''' Celery task that wraps around task.delete_session. This task
    runs according to celery_beat_schedule defined in config.
    '''
    with app.app_context():
        time_now = datetime.datetime.now()
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT urlSlug, createTime FROM sessions WHERE\
                        TIMESTAMPDIFF(HOUR, createTime, CURRENT_TIMESTAMP()) > 48;")
        all_sessions = cursor.fetchall()
        for session in all_sessions:
            try:
                delete_session(session[0])
            except Exception, e:
                delete_session.retry(exc=e, countdown=5)
        app.logger.warning("{} sessions have been deleted.".format(len(all_sessions)))
    return
