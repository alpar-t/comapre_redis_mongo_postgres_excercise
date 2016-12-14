Developing
==========

To see it in action just run ( redis server not required ):

    ./test_end2end.sh

This will check for required tools and run unit, integration and end-to-end 
tests setting up redis and any other environments.
The testing scripts and tests are simple and will help you guide you as to what
is where and how it works.

How The Database was Chosen
===========================

On the hard-coded implementation
--------------------------------

Since all the prefixes are stored in a python hash with 
[O(1)](https://wiki.python.org/moin/DictionaryKeys) access time,
the time complexity is linear with the length of the phone number, 
a finite number, thus the overall time complexity is *O(1)*.

On using MySQL
--------------

### How would it be implemented ?

Could use a `rules` table such as:

    CREATE TABLE rules (
        prefix VARCHAR(15),
        type ENUM('allow', 'restrict') NOT NULL,
        trialOnly BOOLEAN NOT NULL,
        orgId VARCHAR(36) NOT NULL DEFAULT '',
        PRIMARY KEY (orgId, prefix)
    );

The prefix can be part of the primary key, because it doesn't make sense to both restrict 
and allow the same prefix.

Note that the sample queries are for non trial users. 
The queries for trial users would not include such a condition. 

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
 
### How would this perform

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

### Conclusions

- we exchanged an O(1) hash-table based implementation to 
  around O(log(n)) - the B-TREE index time complexity of the database
- the time complexity is much harder to get right, as it's 
  obscured by the database implementation 
- the end query has some obscure parts, like the ordering, 
  that make it hard to understand
- it took significant time and effort to come up with this end query, 
  if the requirements change even a bit it is likely that the mental
  process has to be repeated.

On Using PostgreSQL
-------------------

Unlike MySQL, there is [a hash index](https://www.postgresql.org/docs/9.1/static/indexes-types.html), 
but it suffers from reliability issues, and while the time complexity is not documented
(older versions of the manual)[https://www.postgresql.org/docs/8.3/static/indexes-types.html]
state that performance is not better than B-TREE.

It is unlikely that PostgreSQL can be any better than MySQL in this case.

On using MongoDB
----------------

The concept is similar to MySQL, we would store the rules in a collection:

	db.rules.createIndex(
		{ prefix:1, orgId:1 }, 
		{ unique: true }
	)
	db.rules.insert(
	   { "prefix" : "123", "type" : "allow", "isTrial" : false, orgId: "954e022d-1508-4c51-84f5-85fc4d0dc1f2" }
	)
	db.rules.insert(
	   { "prefix" : "12", "type" : "allow", "isTrial" : false, orgId: "954e022d-1508-4c51-84f5-85fc4d0dc1f2" }
	)
	db.rules.insert(
	   { "prefix" : "12", "type" : "restrict", "isTrial" : false }
	)
	db.rules.insert(
	   { "prefix" : "1", "type" : "allow", "isTrial" : false }
	)

We can the search for the rules in an equivalent way:

	db.rules.find( 
		{ 
			$or: [ { prefix: "1" }, { prefix: "12" }, { prefix: "123" } ],
			isTrial: false,
			$or: [
				{ orgId: '954e022d-1508-4c51-84f5-85fc4d0dc1f2', type: 'allow' },
				{ orgId: { $exists: false } }
			]
		}
	).sort(
		{
			orgId: -1, prefix: -1 
		}
	).limit(1)

It seems that mongoDB insists on a `colscan` even with more than 2600 documents:

		"winningPlan" : {
			"stage" : "SORT",
			"sortPattern" : {
				"orgId" : -1,
				"prefix" : -1
			},
			"limitAmount" : 1,
			"inputStage" : {
				"stage" : "SORT_KEY_GENERATOR",
				"inputStage" : {
					"stage" : "COLLSCAN",

That's also true with a dedicated index on `prefix`, so the time complexity is O(n).

Even if we were to use the database just as a store, and implement a rule processing 
engine in the application, we would get an `IXSCAN` of O(log n) at best:

	db.rules.find( { $or: [ { prefix: "1" }, { prefix: "12" }, { prefix: "123" } ] } ).expain()

	"winningPlan" : {
	"stage" : "SUBPLAN",
	"inputStage" : {
		"stage" : "FETCH",
		"inputStage" : {
			"stage" : "IXSCAN", 

Even if we are to take a latency penalty to get the prefixes one-by-one, the index 
scan can not be avoided with this collection. 
Breaking up in multiple collections and using the prefix as an index might do it, but
that would increase complexity even further, and we would still need to implement a rule
engine in the application, so it would seem an inferior solution to the MySQL one.

On Using Redis
--------------

The data can be modeled in redis:

    hset rules:trial 12 restrict
    hset rules 123 restrict
    hset rules:org 954e022d-1508-4c51-84f5-85fc4d0dc1f2 enable
    hset rules:org 954e022d-1508-4c51-84f5-85fc4d0dc1f2:12 allow

Note: since the number of rules is expected to be moderate, readable values are preferred 
that better reflect intent rather than some more compact variant. 

- The rule engine would need to be implemented by the app, but each rule lookup would
  be of O(1) complexity. 
    - Redis documents the time complexity in a straight forward way.
- a LUA script that runs on Redis can save on latency and bandwidth
    - granted at the expense of making use of a new programming language in the mix
- the data model is compact, straight forward, and reassembles the python implementation,
  making it especially easy to understand for anyone who understood the previous implementation
- We need to store the special `enable` value for organisation IDs so that we can short-circuit 
  the organisational lookups most of the time. 

As redis offers clear time complexity, relatively straight forward implementation, and is also
likely to be the fastest since it operates in memory, it's the best fit for a solution.

References 
===========

- [Wikipedia: Telephone numbering](https://en.wikipedia.org/wiki/Telephone_numbering_plan) 
  states that the maximum length of a phone number is 15
    - [PBX](https://en.wikipedia.org/wiki/Business_telephone_system#Private_branch_exchange) 
      extensions might be additional, but I don't think we need to support those. 

