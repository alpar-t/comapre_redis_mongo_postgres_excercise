On the hard-coded implementation
================================

Since all the prefixes are stored in a python hash with 
[O(1)](https://wiki.python.org/moin/DictionaryKeys) access time,
the time complexity is linear with the length of the phone number, 
a finite number, thus the overall time complexity is *O(1)*.

On using MySQL
==============

How would it be implemented ?
-----------------------------

Could use a `rules` table such as:

    CREATE TABLE rules (
        prefix VARCHAR(15),
        type ENUM('allow', 'restrict') NOT NULL,
        trialOnly BOOLEAN NOT NULL,
        orgId VARCHAR(36) NOT NULL DEFAULT '',
        PRIMARY KEY (orgId, prefix)
    );

    +-----------+---------------------------+------+-----+---------+-------+
    | Field     | Type                      | Null | Key | Default | Extra |
    +-----------+---------------------------+------+-----+---------+-------+
    | prefix    | varchar(15)               | NO   | PRI | NULL    |       |
    | type      | enum('allow','restrict')  | NO   |     | NULL    |       |
    | trialOnly | tinyint(1)                | NO   |     | NULL    |       |
    +-----------+---------------------------+------+-----+---------+-------+

The prefix can be a primary key, because it doesn't make sense to both restrict 
and allow the same prefix.

The query to get all rules would look like:
    
    INSERT INTO rules VALUES ("12", 'allow', false, '');
    INSERT INTO rules VALUES ("123", 'restrict', false, '');

    SELECT type FROM rules
      WHERE prefix IN (:prefixes) 
        AND trialOnly = :trialOnly AND (orgID = :orgID OR orgId IS NUL)

    SELECT prefix, type, orgId FROM rules 
      WHERE prefix IN ("1", "12", "123", "1234", "12345", "123456", "1234567", "12345678", "123456789") 
        AND trialOnly = false
        AND (orgId = '954e022d-1508-4c51-84f5-85fc4d0dc1f2' OR orgId = '');

The application would need to process all the rules and decide, but that 
could also be pushed to the query:

    INSERT INTO rules VALUES ("123", 'allow', false, '954e022d-1508-4c51-84f5-85fc4d0dc1f2');

    SELECT type FROM rules 
      WHERE prefix IN ("1", "12", "123", "1234", "12345", "123456", "1234567", "12345678", "123456789") 
        AND trialOnly = false 
        AND (orgId = '954e022d-1508-4c51-84f5-85fc4d0dc1f2' OR orgId = '')
      ORDER BY CHAR_LENGTH(prefix) DESC, orgId DESC      
      LIMIT 1;

Another example with organisation specific rules:

    INSERT INTO rules VALUES ("24", 'allow', false, '954e022d-1508-4c51-84f5-85fc4d0dc1f2');
    INSERT INTO rules VALUES ("246", 'restrict', false, '');

    SELECT type FROM rules 
      WHERE prefix IN ("2", "24", "246") 
        AND trialOnly = false 
        AND (orgId = '954e022d-1508-4c51-84f5-85fc4d0dc1f2' OR orgId = '')
      ORDER BY orgId DESC, CHAR_LENGTH(prefix) DESC
      LIMIT 1;

The `ORDER BY` clause works because it considers any rule which is organisation specific to triumph, 
and consider the most specific rule ( the one with the longest prefix ) otherwise. 

Note that this does make it possible to restrict a specific organisation as well not only to allow it.
A rule like that would probably be a mistake, and would upset the specific organization, 
would be better to avoid it:

    SELECT type FROM rules 
      WHERE prefix IN ("2", "24", "246") 
        AND trialOnly = false 
        AND (
            (
               orgId = '954e022d-1508-4c51-84f5-85fc4d0dc1f2' AND type = 'allow'
            ) 
            OR orgId = ''
        )        
      ORDER BY orgId DESC, prefix DESC
      LIMIT 1;

This way any organisation specific rule that restricts access is filtered out. 
Of course we could also take measures to make sure these don't get into the database in the first place, 
but since upsetting the customer could mean a lost deal, it's better to have a last line of defense anyway.

How would this perform
----------------------

With around 600 rows, it does use the index:

    +----+-------------+-------+------------+-------+---------------+---------+---------+------+------+----------+-------------+
    | id | select_type | table | partitions | type  | possible_keys | key     | key_len | ref  | rows | filtered | Extra       |
    +----+-------------+-------+------------+-------+---------------+---------+---------+------+------+----------+-------------+
    |  1 | SIMPLE      | rules | NULL       | range | PRIMARY       | PRIMARY | 55      | NULL |    6 |    10.00 | Using where |
    +----+-------------+-------+------------+-------+---------------+---------+---------+------+------+----------+-------------+

Since we were careful with the order of the columns in the primary field, 
it uses it to sort as well (instead of a _filesort_).

This could be optimized further by representing the prefix as an unsigned  BIGINT. 
This can hold any number within 19 chars and some wit 20 - more than sufficient.
Integer operations are faster, and more storage efficient - which can help when data 
has to fit in memory, but would not be of 
significance at the size of this data set. 

Conclusions
-----------

- we exchanged an O(1) hash-table based implementation to 
  around O(log(n)) - the B-TREE index time complexity of the database
- the time complexity is much harder to get right, as it's 
  obscured by the database implementation 
- the end query has some obscure parts, like the ordering, 
  that make it hard to understand
- it took significant time and effort to come up with this end query, 
  if the requirements change even a bit it is likely that the mental
  process has to be repeated.

References 
===========

- [Wikipedia: Telephone numbering](https://en.wikipedia.org/wiki/Telephone_numbering_plan) 
  states that the maximum length of a phone number is 15
    - [PBX](https://en.wikipedia.org/wiki/Business_telephone_system#Private_branch_exchange) 
      extensions might be additional, but I don't think we need to support those. 

On Using PostgreSQL
===================

Unlike MySQL, there is [a hash index](https://www.postgresql.org/docs/9.1/static/indexes-types.html), 
but it suffers from reliability issues, and while the time complexity is not documented
(older versions of the manual)[https://www.postgresql.org/docs/8.3/static/indexes-types.html]
state that performance is not better than B-TREE.

It is unlikely that PostgreSQL can be any better than MySQL in this case.

