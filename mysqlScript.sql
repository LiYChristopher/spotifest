CREATE DATABASE spotifest2;
use spotifest2;

CREATE TABLE sessions (
    festivalId int(10) NOT NULL AUTO_INCREMENT,
    festivalName varchar(100) NOT NULL,
    userId varchar(30) NOT NULL,
    playlistId varchar(30) NOT NULL,
    playlistURL varchar(512) NOT NULL,
    catalogId varchar(30) NOT NULL,
    urlSlug varchar (512) NOT NULL,
    createTime DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (festivalId)
);

CREATE TABLE contributors (
    festivalId int (10) NOT NULL,
    userId varchar(30) NOT NULL,
    ready boolean DEFAULT 0 NOT NULL,
    hotness decimal(4,3),
    danceability decimal(4,3),
    energy decimal(4,3),
    variety decimal(4,3),
    adventurousness decimal(4,3),
    organizer boolean DEFAULT 0 NOT NULL,
    CONSTRAINT FOREIGN KEY (festivalId) REFERENCES sessions(festivalId)
        ON DELETE CASCADE,
      CONSTRAINT festival_user UNIQUE (festivalId, userId)
);

CREATE TABLE users(
    userId varchar(30) NOT NULL,
    PRIMARY KEY (userId)
);

CREATE TABLE festivalArtists (
    userId varchar(30) NOT NULL,
    artist varchar(60) NOT NULL,
    festivalId int(10),
    CONSTRAINT FOREIGN KEY (userId) REFERENCES users(userId)
        ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY (festivalId) REFERENCES sessions(festivalId),
    UNIQUE (userId, artist)
);
