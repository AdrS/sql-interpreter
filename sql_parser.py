import lex
import yacc
import db
from collections import namedtuple

# TODO(adrs): move into function closure or class

keywords = {
	#w.lower() : w.upper() for w in
	'boolean':'BOOLEAN',
	'create':'CREATE',
	'false':'FALSE',
	'float':'FLOAT',
	'insert':'INSERT',
	'integer':'INTEGER',
	'into':'INTO',
	'not':'NOT',
	'null':'NULL',
	'string':'STRING',
	'table':'TABLE',
	'true':'TRUE',
	'values':'VALUES'
}

tokens = (
	'FLOAT_LITERAL',
	'IDENTIFIER',
	'INTEGER_LITERAL',
	'STRING_LITERAL',
) + tuple(keywords.values())

catalog = {}

def SqlLexer():
	literals = ['(', ')', ',', ';']

	def t_COMMENT(t):
		r'--[^\n]*\n'
		pass

	def t_FLOAT_LITERAL(t):
		r'[0-9]+\.[0-9]*'
		t.value = float(t.value)
		return t

	def t_IDENTIFIER(t):
		r'[a-zA-Z][a-zA-Z0-9_]*'
		t.value = t.value.lower()

		t.type = keywords.get(t.value, 'IDENTIFIER')
		return t

	def t_INTEGER_LITERAL(t):
		r'[0-9]+'
		t.value = int(t.value)
		return t

	def t_STRING_LITERAL(t):
		r"'([^'\n]|'')*'"
		t.value = t.value[1:-1].replace("''", "'")
		return t

	t_ignore = ' \t\n'

	def t_error(t):
		print('Unrecocnized character %r' % t)

	return lex.lex()

CreateTable = namedtuple('CreateTable', ['name', 'columns'])
InsertInto = namedtuple('InsertInto', ['table_name', 'tuples'])

def p_statement(p):
	'''statement : insert_into ';'
				| create_table ';' '''
	statement = p[1]
	statement_type = type(statement)
	if statement_type == CreateTable:
		name, columns = statement.name, statement.columns
		catalog[name] = db.MaterialRelation(columns, name)
	elif statement_type == InsertInto:
		table_name, tuples = statement.table_name, statement.tuples
		if table_name not in catalog:
			raise KeyError('Table %r does not exist' % table_name)
		table = catalog[table_name]
		# TODO: move atomic insert logic into MaterialRelation
		checkpoint_index = len(table.rows)
		try:
			for values in tuples:
				table.insert(values)
		except Exception as e:
			table.rows = table.rows[:checkpoint_index]
			raise e

def p_create_table(p):
	'''create_table : CREATE TABLE IDENTIFIER '(' column_list ')' '''
	p[0] = CreateTable(name=p[3], columns=p[5])

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

def p_insert_into(p):
	'''insert_into : INSERT INTO IDENTIFIER VALUES '(' values_list ')' '''
	p[0] = InsertInto(table_name=p[3], tuples=p[6])

def p_values_list_base(p):
	'values_list : tuple_value'
	p[0] = [p[1]]

def p_values_list(p):
	'''values_list : values_list ',' tuple_value'''
	p[1].append(p[3])
	p[0] = p[1]

def p_tuple_value(p):
	'''tuple_value : '(' primative_list ')' '''
	p[0] = p[2]

def p_primative_list_base(p):
	'''primative_list : primative'''
	p[0] = [p[1]]

def p_primative_list(p):
	'''primative_list : primative_list ',' primative'''
	p[1].append(p[3])
	p[0] = p[1]

def p_primative(p):
	'''primative : FLOAT_LITERAL
				| INTEGER_LITERAL
				| STRING_LITERAL
				| NULL
				| TRUE
				| FALSE'''
	if p[1] == 'true':
		p[0] = True
	elif p[1] == 'false':
		p[0] = False
	elif p[1] == 'null':
		p[0] = None
	else:
		p[0] = p[1]

def p_error(p):
	raise ValueError('Syntax error %r' % p)

lexer = SqlLexer()
parser = yacc.yacc()

def execute(sql_command):
	parser.parse(sql_command, lexer=lexer)

# TODO: rename file repl.py

if __name__ == '__main__':
	pass
