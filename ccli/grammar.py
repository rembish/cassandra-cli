from modgrammar import Grammar, WORD, OPTIONAL, OR, LIST_OF, ParseError, GrammarClass, ZERO_OR_MORE, L, Literal
from modgrammar.extras import QuotedString, RE, REGrammar
from modgrammar.util import make_classdict

'''
    See also http://cassandra.apache.org/doc/cql/CQL.html
'''

def CK(string, **kwargs): # Caseless Keyword
    re = ''.join(["[%s%s]" % (c.lower(), c.upper()) for c in string])
    cdict = make_classdict(REGrammar, (), kwargs, regexp=re, grammar_name="CK({0!r})".format(string))
    instance = GrammarClass("CK<%s>" % string, (REGrammar,), cdict)
    instance.keyword = '%s ' % string
    instance.type = 'keyword'
    return instance

def OP(string, **kwargs): # Operator
    cdict = make_classdict(Literal, (), kwargs, string=string, grammar_name="OP({0!r})".format(string))
    instance = GrammarClass("<OPERATOR>", (Literal,), cdict)
    instance.keyword = string
    instance.type = 'operator'
    return instance

def FN(string, **kwargs): # Caseless Function
    re = ''.join(["[%s%s]" % (c.lower(), c.upper()) for c in string])
    cdict = make_classdict(REGrammar, (), kwargs, regexp=re, grammar_name="FN({0!r})".format(string))
    instance = GrammarClass("FN<%s>" % string, (REGrammar,), cdict)
    instance.keyword = '%s(' % string
    instance.type = 'function'
    return instance

class LPar(Grammar):
    grammar = OP('(')

class RPar(Grammar):
    grammar = OP(') ')

class Identifier(Grammar):
    grammar = WORD('a-zA-Z', 'a-zA-Z0-9_')

class StringLiteral(Grammar):
    grammar = QuotedString

class Integer(Grammar):
    grammar = OR(L('0'), (OPTIONAL(L('-')), WORD('1-9', '0-9')))

class UUID(Grammar):
    grammar = RE(r'[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}')

class Float(Grammar):
    grammar = (OPTIONAL(L('-')), WORD('1-9', '0-9'), L('.'), WORD('0-9'))

class StorageType(Grammar):
    grammar = OR(CK('ascii'), CK('bigint'), CK('blob'), CK('boolean'), CK('counter'), CK('decimal'), CK('double'), CK('float'),
        CK('int'), CK('text'), CK('timestamp'), CK('uuid'), CK('varchar'), CK('varint'))

class Term(Grammar):
    grammar = OR(CK('key'), UUID, Identifier, StringLiteral, Float, Integer)

class Name(Grammar):
    grammar = Identifier | StringLiteral | Integer

class Consistency(Grammar):
    grammar = OR(CK('any'), CK('one'), (OPTIONAL(CK('local') | CK('each')), CK('quorum')), CK('all'))

class UseStatement(Grammar):
    grammar = (CK('use'), Term)

class RelationOperator(Grammar):
    grammar = OR(OP('='), OP('<='), OP('>='), OP("<"), OP('>'))

class Relation(Grammar):
    grammar = (Term, RelationOperator, Term)

class SelectWhereClause(Grammar):
    grammar = OR(LIST_OF(Relation, sep=CK('and')), (Term, CK('in'), LPar, LIST_OF(Term), RPar))

class ColumnRange(Grammar):
    grammar = OR((Term, OP('..'), Term), OP('*'))

class CountTarget(Grammar):
    grammar = OR(OP('*'), OP('1'))

class WhatToSelect(Grammar):
    grammar = OR(
        (OPTIONAL(CK('first'), Integer, OPTIONAL(CK('reversed'))), ColumnRange),
        (FN('count'), LPar, CountTarget, RPar), LIST_OF(Term)
    )

class SelectStatement(Grammar):
    grammar = (
        CK('select'), WhatToSelect, CK('from'), OPTIONAL(Name, OP('.')), Name,
        OPTIONAL(CK('using'), CK('consistency'), Consistency),
        OPTIONAL(CK('where'), SelectWhereClause),
        OPTIONAL(CK('limit'), Integer)
    )

class DeleteOption(Grammar):
    grammar = OR((CK('consistency'), Consistency), (CK('timestamp'), Integer))

class UsingOption(Grammar):
    grammar = OR(DeleteOption, (CK('ttl'), Integer))

class UsingClause(Grammar):
    grammar = (CK('using'), LIST_OF(UsingOption, sep=CK('and')))

class InsertStatement(Grammar):
    grammar = (CK('insert'), CK('into'), Name, LPar, LIST_OF(Term), RPar, CK('values'), LPar, LIST_OF(Term), RPar, OPTIONAL(UsingClause))

class UpdateWhereClause(Grammar):
    grammar = OR((Term, OP('='), Term), (Term, CK('in'), LPar, LIST_OF(Term), RPar))

class Assignment(Grammar):
    grammar = OR(
        (Term, OP('='), Term, OP('+'), Term),
        (Term, OP('='), Term, OP('-'), Term),
        (Term, OP('='), Term),
    )

class UpdateStatement(Grammar):
    grammar = (CK('update'), Name, OPTIONAL(UsingClause), CK('set'), LIST_OF(Assignment), CK('where'), UpdateWhereClause)

class DeleteStatement(Grammar):
    grammar = (CK('delete'), OPTIONAL(LIST_OF(Term)), CK('from'), Name, OPTIONAL(CK('using'), LIST_OF(DeleteOption, sep=CK('and'))), CK('where'), UpdateWhereClause)

class TruncateStatement(Grammar):
    grammar = (CK('truncate'), Name)

class BatchStatementMember(Grammar):
    grammar = OR(InsertStatement, UpdateStatement, DeleteStatement)

class BatchStatement(Grammar):
    grammar = (CK('begin'), CK('batch'), OPTIONAL(UsingClause), LIST_OF(BatchStatementMember, sep=';'), CK('apply'), CK('batch'))

class OptionName(Grammar):
    grammar = LIST_OF(Identifier, sep=':')

class OptionValue(Grammar):
    grammar = OR(StringLiteral, Identifier, Integer)
    
class CreateKeyspaceStatement(Grammar):
    grammar = (CK('create'), CK('keyspace'), Name, CK('with'), LIST_OF((OptionName, OP('='), OptionValue), sep=CK('and')))
    
class ColumFamilyOptionValue(Grammar):
    grammar = OR(StorageType, Identifier, StringLiteral, Float, Integer)
    
class CreateColumnFamilyStatement(Grammar):
    grammar = (
        CK('create'), CK('columnfamily'), Name, LPar, Term, StorageType, CK('primary'), CK('key'),
        ZERO_OR_MORE((OP(','), Term, StorageType)), RPar,
        OPTIONAL(CK('with'), LIST_OF((Identifier, OP('='), ColumFamilyOptionValue), sep=CK('and')))
    )

class CreateIndexStatement(Grammar):
    grammar = (CK('create'), CK('index'), OPTIONAL(Identifier), CK('on'), Name, LPar, Term, RPar)

class DropKeyspaceStatement(Grammar):
    grammar = (CK('drop'), CK('keyspace'), Name)

class DropColumnFamilyStatement(Grammar):
    grammar = (CK('drop'), CK('columnfamily'), Name)

class DropIndexStatement(Grammar):
    grammar = (CK('drop'), CK('index'), Name)

class AlterInstructions(Grammar):
    grammar = OR(
        (CK('alter'), Name, CK('type'), StorageType),
        (CK('add'), Name, StorageType),
        (CK('drop'), Name)
    )

class AlterColumnFamilyStatement(Grammar):
    grammar = (CK('alter'), CK('columnfamily'), Name, AlterInstructions)

class QuitStatement(Grammar):
    grammar = OR(CK('quit'), CK('exit'))

class SchemaChangeStatement(Grammar):
    grammar = OR(
        CreateKeyspaceStatement, CreateColumnFamilyStatement, CreateIndexStatement,
        DropKeyspaceStatement, DropColumnFamilyStatement, DropIndexStatement,
        AlterColumnFamilyStatement
    )

class DataChangeStatement(Grammar):
    grammar = OR(InsertStatement, UpdateStatement, BatchStatement, DeleteStatement, TruncateStatement)

class ClientStatement(Grammar):
    grammar = OR(QuitStatement)

class StatementBody(Grammar):
    grammar = OR(UseStatement, SelectStatement, DataChangeStatement, SchemaChangeStatement, ClientStatement)

class Statement(Grammar):
    grammar = (StatementBody, OP(';'))

if __name__ == '__main__':
    tests = [
        "USE myApp;",
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

    #for row in generate_ebnf(Statement):
    #    print row.rstrip()

    parser = Statement.parser()
    try:
        parser.parse_string('', eof=True)
    except ParseError as e:
        print [t.keyword for t in e.expected if t.grammar_name[:2] in ['OP', 'CK']]

    for test in tests:
        parser.reset()
        print test
        try:
            print 'OK', parser.parse_string(test, eof=True).terminals()
        except ParseError as e:
            raise Exception(e.message)
