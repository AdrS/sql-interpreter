import lex
import yacc
import relation
from collections import namedtuple

keywords = {
	#w.lower() : w.upper() for w in
	'and':'AND',
	'boolean':'BOOLEAN',
	'create':'CREATE',
	'false':'FALSE',
	'float':'FLOAT',
	'from':'FROM',
	'insert':'INSERT',
	'integer':'INTEGER',
	'into':'INTO',
	'not':'NOT',
	'null':'NULL',
	'or':'OR',
	'select':'SELECT',
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
	'LEQ',
	'GEQ',
	'NEQ',
) + tuple(keywords.values())

precedence = (
	('left', 'OR'),
	('left', 'AND'),
	('nonassoc', '<', '>', '=', 'LEQ', 'GEQ', 'NEQ'),
	('left', '+', '-'),
	('left', '*', '/')
)

# TODO: NOT and unary minus

def SqlLexer():
	literals = ['(', ')', ',', ';', '*', '+', '-', '*', '/', '<', '=', '>']

	t_LEQ = r'<='
	t_GEQ = r'>='
	t_NEQ = r'(<>)|(!=)'

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

def p_statement(p):
	'''statement : insert_statement ';'
				| create_table_statement ';'
				| select_statement ';'
	'''
	p[0] = p[1]

def p_create_table_statement(p):
	'''create_table_statement : CREATE TABLE IDENTIFIER '(' column_list ')' '''
	p[0] = CreateTableNode(name=p[3], columns=p[5])

def p_column_list_base(p):
	'''column_list : column_definition'''
	p[0] = [p[1]]

def p_column_list(p):
	'''column_list : column_list ',' column_definition'''
	p[1].append(p[3])
	p[0] = p[1]

def p_primitive_type(p):
	'''primitive_type : BOOLEAN
						| FLOAT
						| INTEGER
						| STRING'''
	types_by_name = {
		'integer':int,
		'float':float,
		'boolean':bool,
		'string':str,
	}
	p[0] = types_by_name[p[1]]

def p_column_definition(p):
	'''column_definition : IDENTIFIER primitive_type nullability_definition '''
	column_name = p[1]
	column_type = p[2]
	nullability = p[3]
	p[0] = relation.Column(column_name, column_type, nullability)

def p_nullable(p):
	'''nullability_definition : empty
							| NULL
							| NOT NULL'''
	p[0] = len(p) != 3

def p_insert_statement(p):
	'''insert_statement : INSERT INTO IDENTIFIER VALUES '(' values_list ')' '''
	p[0] = InsertIntoNode(table_name=p[3], tuples=p[6])

def p_values_list_base(p):
	'values_list : tuple_value'
	p[0] = [p[1]]

def p_values_list(p):
	'''values_list : values_list ',' tuple_value'''
	p[1].append(p[3])
	p[0] = p[1]

def p_tuple_value(p):
	'''tuple_value : '(' primitive_list ')' '''
	p[0] = p[2]

def p_primitive_list_base(p):
	'''primitive_list : primitive'''
	p[0] = [p[1]]

def p_primitive_list(p):
	'''primitive_list : primitive_list ',' primitive'''
	p[1].append(p[3])
	p[0] = p[1]

def p_primitive(p):
	'''primitive : FLOAT_LITERAL
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

def p_expression_constant(p):
	'''expression_constant : primitive'''
	p[0] = ConstantNode(p[1])

def p_select_statement(p):
	'''select_statement : SELECT select_expression_list FROM IDENTIFIER'''
	p[0] = SelectNode(select_expressions=p[2], table=p[4])

def p_select_expression_list_base(p):
	'''select_expression_list : select_expression'''
	p[0] = [p[1]]

def p_select_expression_list(p):
	'''select_expression_list : select_expression_list ',' select_expression'''
	p[1].append(p[3])
	p[0] = p[1]

def p_select_expression(p):
	'''select_expression : wildcard
						| expression'''
	p[0] = p[1]

def p_wildcard(p):
	'''wildcard : '*' '''
	# TODO: tablename.*
	p[0] = ColumnReferenceNode(table_name=None, column_name='*')

def p_expression(p):
	'''expression : expression_constant
					| column_reference
					| '(' expression ')'
	'''
	if p[1] == '(':
		p[0] = p[2]
	else:
		p[0] = p[1]

	# | '-' expression
	# | NOT expression
	# TODO: IS NULL, IS NOT NULL

def p_expression_binary_operator(p):
	'''expression :   expression '+' expression
					| expression '-' expression
					| expression '*' expression
					| expression '/' expression
					| expression '<' expression
					| expression LEQ expression
					| expression '=' expression
					| expression NEQ expression
					| expression GEQ expression
					| expression '>' expression
					| expression AND expression
					| expression OR expression
	'''
	p[0] = BinaryOperationNode(p[2], p[1], p[3])

# def p_expression_unary_operator(p):
# 	'''expression : NOT expression
# 					| '-' expression'''

def p_column_reference(p):
	'''column_reference : IDENTIFIER'''
	p[0] = ColumnReferenceNode(table_name=None, column_name=p[1])

def p_column_reference_fully_qualified(p):
	'''column_reference : IDENTIFIER '.' IDENTIFIER'''
	p[0] = ColumnReferenceNode(table_name=p[1], column_name=p[3])

def p_empty(p):
	'empty :'
	pass

def p_error(p):
	raise ValueError('Syntax error %r' % p)

lexer = SqlLexer()
parser = yacc.yacc()

class AstNode:
	def compile(self, **kwargs):
		raise NotImplemented

class ExpressionNode(AstNode):
	def compile(self, table, used_columns):
		'''
		Updates used columns to include all columns referenced by the
		expression.
		'''
		raise NotImplemented

class ConstantNode(ExpressionNode):
	def __init__(self, value):
		self.value = value

	def compile(self, table):
		return relation.Constant(self.value)

class ColumnReferenceNode(ExpressionNode):
	def __init__(self, table_name, column_name):
		self.table_name = table_name
		self.column_name = column_name

	def is_wildcard(self):
		return self.column_name == '*'

	def expand_wildcard(self, table):
		columns = []
		for column in table.columns:
			columns.append(ColumnReferenceNode(self.table_name, column.name))
		return columns

	def compile(self, table):
		# TODO: handle *
		# TODO: support expressions referencing multiple tables
		return relation.Attribute(table.get_column(self.column_name))

class BinaryOperationNode(ExpressionNode):
	def __init__(self, op, lhs, rhs):
		self.op = op
		self.lhs = lhs
		self.rhs = rhs

	def compile(self, table):
		lhs = self.lhs.compile(table)
		rhs = self.rhs.compile(table)
		if self.op == 'and':
			return relation.And(lhs, rhs)
		if self.op == 'or':
			return relation.Or(lhs, rhs)
		if self.op in ['<', '<=', '<>', '!=', '=', '>=', '>']:
			return relation.Comparison(self.op, lhs, rhs)
		if self.op in ['+', '-', '*', '/']:
			return relation.Arithmetic(self.op, lhs, rhs)
		raise ValueError('Unknown binary operator %r' % self.op)

CreateTableNode = namedtuple('CreateTableNode', ['name', 'columns'])
InsertIntoNode = namedtuple('InsertIntoNode', ['table_name', 'tuples'])
SelectNode = namedtuple('SelectNode', [
	'select_expressions',
	'table'
])


class Db:
	def __init__(self):
		self.catalog = {}

	def __execute_create_table(self, node):
		name, columns = node.name, node.columns
		self.catalog[name] = relation.MaterialRelation(columns, name)

	def __execute_insert(self, node):
		table_name, tuples = node.table_name, node.tuples
		if table_name not in self.catalog:
			raise KeyError('Table %r does not exist' % table_name)
		table = self.catalog[table_name]
		# TODO: move atomic insert logic into MaterialRelation
		checkpoint_index = len(table.rows)
		try:
			for values in tuples:
				table.insert(values)
		except Exception as e:
			table.rows = table.rows[:checkpoint_index]
			raise e

	def __execute_select(self, node):
		# TODO: move into SelectNode.compile
		table = self.catalog[node.table]
		select_expressions = []
		for expression in node.select_expressions:
			if (type(expression) == ColumnReferenceNode and
				expression.is_wildcard()):
				select_expressions.extend(expression.expand_wildcard(table))
			else:
				select_expressions.append(expression)
			
		expressions = [
			expression.compile(table) for expression in select_expressions]
		return relation.GeneralizedProjection(table, expressions)

	def execute(self, sql_command):
		ast_root = parser.parse(sql_command, lexer=lexer)
		statement_type = type(ast_root)
		if statement_type == CreateTableNode:
			self.__execute_create_table(ast_root)
		elif statement_type == InsertIntoNode:
			self.__execute_insert(ast_root)
		elif statement_type == SelectNode:
			return self.__execute_select(ast_root)
		else:
			raise TypeError('Unknown AST node type')

if __name__ == '__main__':
	pass
