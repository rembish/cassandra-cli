from pyparsing import Literal, Word, Optional, QuotedString, Combine, restOfLine, CaselessKeyword, delimitedList, ZeroOrMore, Group, Empty
from pyparsing import cppStyleComment, dblSlashComment
from pyparsing import alphas, alphanums, nums, hexnums

unary_minus = Literal('-')

comment_inline = (Literal('--')  + restOfLine) | dblSlashComment
comment_multi = cppStyleComment

identifier = Combine(Word(alphas) + Optional(Word(alphanums + '_')))
string_literal = QuotedString(quoteChar="'", escChar="''", multiline=False)
integer = Combine(Optional(unary_minus) + Word(nums))
uuid = Combine(
    Word(hexnums, exact=8) + Literal('-') + Word(hexnums, exact=4) + Literal('-') +
    Word(hexnums, exact=4) + Literal('-') + Word(hexnums, exact=4) + Literal('-') +
    Word(hexnums, exact=12)
)
float = Combine(Optional(unary_minus) + Word(nums) + Literal('.') + Word(nums))

storage_type = CaselessKeyword('ascii') | CaselessKeyword('bigint') | CaselessKeyword('blob') \
    | CaselessKeyword('boolean') | CaselessKeyword('counter') | CaselessKeyword('decimal') | CaselessKeyword('double') \
    | CaselessKeyword('float') | CaselessKeyword('int') | CaselessKeyword('text') | CaselessKeyword('timestamp') \
    | CaselessKeyword('uuid') | CaselessKeyword('varchar') | CaselessKeyword('varint')

term = CaselessKeyword("key") | uuid | identifier | string_literal | float | integer
name = identifier | string_literal | integer

consistency = CaselessKeyword('any') | CaselessKeyword('one') | (Optional(CaselessKeyword('local') \
    | CaselessKeyword('each')) + CaselessKeyword('quorum')) | CaselessKeyword('all')

use_statement = CaselessKeyword('use') + term

relation_operator = Literal('=') | Literal('<=') | Literal('>=') | Literal('<') | Literal('>')
relation = Group(term + relation_operator + term)
select_where_clause = Group(delimitedList(relation, delim=CaselessKeyword('and'))) \
    | Group(term + CaselessKeyword('in') + Literal('(') + Group(delimitedList(term)) + Literal(')'))
column_range = Group(term + Literal('..') + term) | Literal('*')
count_target = Literal('*') | Literal('1')
what_to_select = (Optional(CaselessKeyword('first') + integer) + Optional(CaselessKeyword('reversed')) + column_range) \
    | (CaselessKeyword('count') + Literal('(') + count_target + Literal(')')) \
    | Group(delimitedList(term))
select_statement = CaselessKeyword('select') + what_to_select + CaselessKeyword('from') + Group(Optional(name + Literal('.')) + name) \
    + Optional(CaselessKeyword('using') + CaselessKeyword('consistency') + consistency) \
    + Optional(CaselessKeyword('where') + select_where_clause) + Optional(CaselessKeyword('limit') + integer)

delete_option = Group(CaselessKeyword('consistency') + consistency) | Group(CaselessKeyword('timestamp') + integer)
using_option =  delete_option | Group(CaselessKeyword('ttl') + integer)
using_clause = CaselessKeyword('using') + Group(delimitedList(using_option, delim=CaselessKeyword('and')))
insert_statement = CaselessKeyword('insert') + CaselessKeyword('into') + name + Literal('(') + Group(delimitedList(term)) \
    + Literal(')') + CaselessKeyword('values') + Literal('(') + Group(delimitedList(term)) + Literal(')') \
    + Optional(using_clause)

update_where_clause = (term + Literal('=') + term) | (term + CaselessKeyword('in') + Literal('(') + Group(delimitedList(term)) \
    + Literal(')'))
assignment = Group(term + Literal('=') + term + Literal('+') + term) \
    | Group(term + Literal('=') + term + Literal('-') + term) \
    | Group(term + Literal('=') + term)
update_statement = CaselessKeyword('update') + name + Optional(using_clause) + CaselessKeyword('set') \
    + Group(delimitedList(assignment)) + CaselessKeyword('where') + Group(update_where_clause)

delete_statement = CaselessKeyword('delete') + (CaselessKeyword('from') + Group(Empty()) \
    | (Optional(Group(delimitedList(term))) + CaselessKeyword('from'))) + name \
    + Optional(CaselessKeyword('using') + Group(delimitedList(delete_option, delim=CaselessKeyword('and')))) \
    + CaselessKeyword('where') + Group(update_where_clause)

truncate_statement = CaselessKeyword('truncate') + name

batch_statement_member = insert_statement | update_statement | delete_statement
batch_statement = CaselessKeyword('begin') + CaselessKeyword('batch') + Optional(using_clause) \
    + Group(delimitedList(batch_statement_member, delim=';')) + CaselessKeyword('apply') + CaselessKeyword('batch')

option_name = Group(delimitedList(identifier, delim=':'))
option_value = string_literal | identifier | integer
create_keyspace_statement = CaselessKeyword('create') + CaselessKeyword('keyspace') + name + CaselessKeyword('with') \
    + Group(delimitedList(Group(option_name + Literal('=') + option_value), delim=CaselessKeyword('and')))

column_family_option_value = storage_type | identifier | string_literal | float | integer
create_column_family_statement = CaselessKeyword('create') + CaselessKeyword('columnfamily') + name \
    + Literal('(') + Group(Group(term + storage_type + CaselessKeyword('primary') + CaselessKeyword('key')) \
    + ZeroOrMore(Group(Literal(',').suppress() + term + storage_type))) + Literal(')') + Optional(CaselessKeyword('with') \
    + Group(delimitedList(Group(identifier + Literal('=') + column_family_option_value), delim=CaselessKeyword('and'))))

create_index_statement = CaselessKeyword('create') + CaselessKeyword('index') + (CaselessKeyword('on') | identifier \
    + CaselessKeyword('on')) + name + Literal('(') + term + Literal(')')

drop_keyspace_statement = CaselessKeyword('drop') + CaselessKeyword('keyspace') + name
drop_column_family_statement = CaselessKeyword('drop') + CaselessKeyword('columnfamily') + name
drop_index_statement = CaselessKeyword('drop') + CaselessKeyword('index') + name

alter_instructions = (CaselessKeyword('alter') + name + CaselessKeyword('type') + storage_type) \
    | (CaselessKeyword('add') + name + storage_type) | (CaselessKeyword('drop') + name)
alter_column_family_statement = CaselessKeyword('alter') + CaselessKeyword('columnfamily') + name + alter_instructions

schema_change_statement = create_keyspace_statement | create_column_family_statement | create_index_statement \
    | drop_keyspace_statement | drop_column_family_statement | drop_index_statement | alter_column_family_statement
data_change_statement = insert_statement | update_statement | batch_statement | delete_statement | truncate_statement
statement_body = use_statement | select_statement | data_change_statement | schema_change_statement
statement = statement_body + Literal(';')

if __name__ == '__main__':
    tests = [
        "SELECT Name, Occupation FROM People WHERE key IN (199, 200, 207);",
        "SELECT FIRST 3 REVERSED 'time199'..'time100' FROM Events;",
        "SELECT COUNT(*) FROM system.Migrations;",
        "select * from foo using consistency quorum;",
        "select a, b from bar where key = 12345 and column = 'egg';",
        "select first 3 o..p from egg where key >= 'am' and key <= 'bz' and module = 'foo';",
        "select count(1) from ham where k in ('a', 'b', 'c') limit 2;",

        "INSERT INTO NerdMovies (KEY, 11924) VALUES ('Serenity', 'Nathan Fillion') USING CONSISTENCY LOCAL QUORUM AND TTL 86400;",

        "UPDATE NerdMovies USING CONSISTENCY ALL AND TTL 400 SET 'A 1194' = 'The Empire Strikes Back', 'B 1194' = 'Han Solo' WHERE KEY = B70DE1D0-9908-4AE3-BE34-5573E5B09F14;",
        "UPDATE UserActionCounts SET total = total + 2 WHERE keyalias = 523;",
        "update ham set baz = 34 + 2 where key in (a, b, c);",

        "DELETE col1, col2, col3 FROM Planeteers USING CONSISTENCY ONE WHERE KEY = 'Captain';",
        "DELETE FROM MastersOfTheUniverse WHERE KEY IN ('Man-At-Arms', 'Teela');",

        "TRUNCATE super_important_data;",

        """BEGIN BATCH USING CONSISTENCY QUORUM AND TTL 8640000
  INSERT INTO users (KEY, password, name) VALUES ('user2', 'ch@ngem3b', 'second user');
  UPDATE users SET password = 'ps22dhds' WHERE KEY = 'user2';
  INSERT INTO users (KEY, password) VALUES ('user3', 'ch@ngem3c');
  DELETE name FROM users WHERE key = 'user2';
  INSERT INTO users (KEY, password, name) VALUES ('user4', 'ch@ngem3c', 'Andrew')
APPLY BATCH;""",

        "CREATE KEYSPACE Excelsior WITH strategy_class = 'SimpleStrategy' AND strategy_options:replication_factor = 1;",
        "CREATE KEYSPACE Excalibur WITH strategy_class = 'NetworkTopologyStrategy' AND strategy_options:DC1 = 1 AND strategy_options:DC2 = 3;",

        "CREATE COLUMNFAMILY Fish (KEY blob PRIMARY KEY);",
        "CREATE COLUMNFAMILY FastFoodEatings (user text PRIMARY KEY) WITH comparator=timestamp AND default_validation=int;",
        """CREATE COLUMNFAMILY MonkeyTypes (
  KEY uuid PRIMARY KEY,
  species text,
  alias text,
  population varint
) WITH comment='Important biological records'
  AND read_repair_chance = 1.0;""",

        "CREATE INDEX userIndex ON NerdMovies (user);",
        "CREATE INDEX ON Mutants (abilityId);",

        "DROP KEYSPACE MyTwitterClone;",
        "DROP COLUMNFAMILY worldSeriesAttendees;",
        "DROP INDEX cf_col_idx;",

        "ALTER COLUMNFAMILY addamsFamily ALTER lastKnownLocation TYPE uuid;",
        "ALTER COLUMNFAMILY addamsFamily ADD gravesite varchar;",
        "ALTER COLUMNFAMILY addamsFamily DROP gender;",
    ]

    for test in tests:
        statement.parseString(test)
