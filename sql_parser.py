import lex
import yacc
import db

# TODO(adrs): move into function closure or class

keywords = {
	#w.lower() : w.upper() for w in
	'boolean':'BOOLEAN',
	'create':'CREATE',
	'float':'FLOAT',
	'integer':'INTEGER',
	'not':'NOT',
	'null':'NULL',
	'string':'STRING',
	'table':'TABLE'
}

tokens = (
	'IDENTIFIER',
) + tuple(keywords.values())

catalog = {}

def SqlLexer():
	literals = ['(', ')', ',', ';']

	def t_IDENTIFIER(t):
		r'[a-zA-Z][a-zA-Z0-9_]*'
		t.value = t.value.lower()

		t.type = keywords.get(t.value, 'IDENTIFIER')
		return t

	def t_COMMENT(t):
		r'--[^\n]*\n'
		pass

	t_ignore = ' \t\n'

	def t_error(t):
		print('Unrecocnized character %r' % t)

	return lex.lex()

def p_create_table(p):
	'''create_table : CREATE TABLE IDENTIFIER '(' column_list ')' ';' '''
	table_name = p[3]
	columns = p[5]
	catalog[table_name] = p[0] = db.Relation(columns, table_name)

def p_column_list_base(p):
	'''column_list : column_definition'''
	p[0] = [p[1]]

def p_column_list(p):
	'''column_list : column_list ',' column_definition'''
	p[1].append(p[3])
	p[0] = p[1]

def p_column_definition(p):
	'''column_definition : IDENTIFIER BOOLEAN nullability_definition
					| IDENTIFIER FLOAT nullability_definition
					| IDENTIFIER INTEGER nullability_definition
					| IDENTIFIER STRING nullability_definition'''
	column_name = p[1]
	types_by_name = {
		'integer':int,
		'float':float,
		'boolean':bool,
		'string':str,
	}
	column_type = types_by_name[p[2]]
	nullability = p[3]
	p[0] = db.Column(column_name, column_type, nullability)

def p_empty(p):
	'empty :'
	pass

def p_nullable(p):
	'''nullability_definition : empty
							| NULL
							| NOT NULL'''
	p[0] = len(p) != 3

# TODO(adrs): insert into <table name> values ...;

def p_error(p):
	print('Syntax error', p)

lexer = SqlLexer()
parser = yacc.yacc()

if __name__ == '__main__':
	pass
