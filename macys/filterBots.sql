DROP TABLE IF EXISTS Sessions;
CREATE TABLE Sessions(sessionId INT, productId INT, PRIMARY KEY (sessionId, productId));
