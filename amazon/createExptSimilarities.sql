DROP TABLE IF EXISTS ExptSimilarities;
CREATE TABLE ExptSimilarities AS
SELECT * FROM Similarities
WHERE NumUsers1 > 500
AND NumUsers2 > 500
AND NumUsersCommon > 100;
