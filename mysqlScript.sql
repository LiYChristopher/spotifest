CREATE DATABASE festify;
use festify;
CREATE TABLE sessions (
    festivalId int(10) NOT NULL AUTO_INCREMENT,
    festivalName varchar(100) NOT NULL,
    userID varchar(30) NOT NULL,
    playlistId varchar(30) NOT NULL,
    playlistURL varchar(512) NOT NULL,
    catalogId varchar(30) NOT NULL,
    urlSlug varchar (512) NOT NULL,
    PRIMARY KEY (festivalId)
);
CREATE table contributors (
    festivalId int (10) NOT NULL,
    userID varchar(30) NOT NULL,
    CONSTRAINT FOREIGN KEY (festivalId) REFERENCES sessions(festivalId)
);

