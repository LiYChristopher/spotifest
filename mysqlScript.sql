CREATE DATABASE festify;
use festify;
CREATE TABLE sessions (
    festivalId int(10) NOT NULL AUTO_INCREMENT,
    userID varchar(30),
    playlistId varchar(30),
    playlistURL varchar(512),
    catalogId varchar(30),
    PRIMARY KEY (festivalId)
);
