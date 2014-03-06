DROP TABLE IF EXISTS ExptSimilarities2;
CREATE TABLE ExptSimilarities2 AS
SELECT * FROM Similarities
WHERE NumUsers1 > 400
AND NumUsers2 > 400
AND NumUsersCommon > 40;
