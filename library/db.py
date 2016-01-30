from library.app import mysql


def save_to_database(userId, playlistId, playlistURL, catalogId):
    '''
    saves infromation the data base.
    festivalId will be created automatically
    '''
    connection = mysql.get_db()
    cursor = connection.cursor()
    query = 'INSERT INTO sessions (userId, playlistId, playlistURL, catalogId) VALUES (\'' + userId + '\', \'' + playlistId + '\', \'' + playlistURL + '\', \'' + catalogId + '\');'
    cursor.execute(query)
    connection.commit()
    print 'saved to database'
    return


def get_info_from_database(festivalId):
    '''
    return a list with all the information from the
    database for a certain festival id
    '''
    connection = mysql.get_db()
    cursor = connection.cursor()
    query = 'SELECT * FROM sessions WHERE festivalId = ' + str(festivalId) + ';'
    cursor.execute(query)
    data = cursor.fetchall()
    festivalId = int(data[0][0])
    userId = str(data[0][1])
    playlistId = str(data[0][2])
    playlistURL = str(data[0][3])
    catalogId = str(data[0][4])
    values = [festivalId, userId, playlistId, playlistURL, catalogId]
    return values
