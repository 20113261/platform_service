SELECT * INTO OUTFILE '/search/hourong/tmp/data.txt'
FIELDS TERMINATED BY ','
FROM pic_relation;

SELECT * INTO OUTFILE '/search/hourong/tmp/data_0905.txt'
FIELDS TERMINATED BY ','
FROM pic_relation_0905;

LOAD DATA INFILE '/search/hourong/tmp/data.txt' REPLACE INTO TABLE pic_relation_total
FIELDS TERMINATED BY ',';