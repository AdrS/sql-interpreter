import lex
import yacc
import relation
from collections import namedtuple

keywords = {
	#w.lower() : w.upper() for w in
	'all':'ALL',
	'and':'AND',
	'as':'AS',
	'boolean':'BOOLEAN',
	'by': 'BY',
	'cast':'CAST',
	'create':'CREATE',
	'distinct':'DISTINCT',
	'false':'FALSE',
	'float':'FLOAT',
	'from':'FROM',
	'group':'GROUP',
	'insert':'INSERT',
	'integer':'INTEGER',
	'intersect':'INTERSECT',
	'into':'INTO',
	'is':'IS',
	'not':'NOT',
	'null':'NULL',
	'or':'OR',
	'select':'SELECT',
	'string':'STRING',
	'table':'TABLE',
	'true':'TRUE',
	'union':'UNION',
	'values':'VALUES',
	'where':'WHERE'
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
	('left', 'UNION'), # except has same precdence
	('left', 'INTERSECT'),
	('left', 'OR'),
	('left', 'AND'),
	('nonassoc', '<', '>', '=', 'LEQ', 'GEQ', 'NEQ'),
	('left', '+', '-'),
	('left', '*', '/')
)

def SqlLexer():
	literals = ['(', ')', ',', ';', '.', '*', '+', '-', '*', '/', '<', '=', '>']

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
				| query_statement ';'
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

def p_query_statement(p):
	'query_statement : select_statement'
	p[0] = p[1]

def p_distinctness(p):
	'''distinctness : empty
				| ALL
				| DISTINCT'''
	if p[1] == 'all':
		p[0] = 'all'
	elif p[1] == 'distinct':
		p[0] = 'distinct'
	else:
		p[0] = None

def p_query_statement_set_op(p):
	'''query_statement : query_statement UNION distinctness query_statement
					| query_statement INTERSECT distinctness query_statement
	'''
	op = p[2]
	distinct = p[3] != 'all'
	p[0] = SetOperatorNode(op, p[1], p[4], distinct)

def p_select_statement(p):
	'''select_statement : SELECT select_expression_list FROM table_expressions where_clause group_by_clause'''
	p[0] = SelectNode(select_expressions=p[2], tables=p[4], where_predicate=p[5], group_by=p[6])

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

def p_tables_expressions_base(p):
	'''table_expressions : table_expression'''
	p[0] = [p[1]]

def p_tables_expressions(p):
	'''table_expressions : table_expressions ',' table_expression'''
	p[1].append(p[3])
	p[0] = p[1]

def p_table_expression_name(p):
	'''table_expression : IDENTIFIER'''
	p[0] = SelectTableNode(table=p[1], alias=None)

def p_table_expression_short_alias(p):
	'''table_expression : IDENTIFIER IDENTIFIER'''
	p[0] = SelectTableNode(table=p[1], alias=p[2])

def p_table_expression_alias(p):
	'''table_expression : IDENTIFIER AS IDENTIFIER'''
	p[0] = SelectTableNode(table=p[1], alias=p[3])

# TODO: subqueries as tables

def p_where_clause_missing(p):
	'''where_clause : empty'''
	p[0] = None

def p_where_clause(p):
	'''where_clause : WHERE expression'''
	p[0] = p[2]

def p_group_by_clause_missing(p):
	'''group_by_clause : empty'''
	p[0] = []

def p_group_by_clause(p):
	'''group_by_clause : GROUP BY column_reference_list'''
	p[0] = p[3]

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

def p_expression_function_evaluation(p):
	'''expression : IDENTIFIER '(' expression ')' '''
	p[0] = FunctionEvaluationNode(name=p[1], argument=p[3])

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

def p_expression_unary_prefix_operator(p):
	'''expression : NOT expression
					| '-' expression'''
	p[0] = UnaryOperationNode(p[1], p[2])

def p_expression_unary_postfix_operator(p):
	'''expression : expression IS NULL
					| expression IS NOT NULL'''
	if p[3] == 'null':
		p[0] = UnaryOperationNode('is null', p[1])
	else:
		p[0] = UnaryOperationNode('is not null', p[1])

def p_expression_cast(p):
	'''expression : CAST '(' expression AS primitive_type ')' '''
	p[0] = CastNode(p[3], p[5])

def p_column_reference(p):
	'''column_reference : IDENTIFIER'''
	p[0] = ColumnReferenceNode(table_name=None, column_name=p[1])

def p_column_reference_fully_qualified(p):
	'''column_reference : IDENTIFIER '.' IDENTIFIER'''
	p[0] = ColumnReferenceNode(table_name=p[1], column_name=p[3])

def p_column_reference_list_base(p):
	'''column_reference_list : column_reference'''
	p[0] = [p[1]]

def p_column_reference_list(p):
	'''column_reference_list : column_reference_list ',' column_reference'''
	p[1].append(p[3])
	p[0] = p[1]

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
	def compile(self, env, used_columns):
		'''
		Updates used columns to include all columns referenced by the
		expression.
		'''
		raise NotImplemented

class ConstantNode(ExpressionNode):
	def __init__(self, value):
		self.value = value

	def compile(self, env):
		return relation.Constant(self.value)

class ColumnReferenceNode(ExpressionNode):
	def __init__(self, table_name, column_name):
		self.table_name = table_name
		self.column_name = column_name

	def is_wildcard(self):
		return self.column_name == '*'

	def expand_wildcard(self, column_mappings):
		columns = []
		for table_name, column in column_mappings.columns:
			columns.append(ColumnReferenceNode(table_name, column.name))
		return columns

	def compile(self, column_mappings):
		return relation.Attribute(column_mappings.get_column(self))

class FunctionEvaluationNode(ExpressionNode):
	def __init__(self, name, argument):
		self.name = name
		self.argument = argument
		self.attribute_access = None

	def compile(self, column_mappings):
		return self.attribute_access

	def get_aggregation(self, column_mappings):
		if self.name == 'count':
			return relation.CountFactory(self.argument.compile(column_mappings))
		if self.name == 'max':
			return relation.MaxFactory(self.argument.compile(column_mappings))
		if self.name == 'min':
			return relation.MinFactory(self.argument.compile(column_mappings))
		if self.name == 'sum':
			return relation.SumFactory(self.argument.compile(column_mappings))
		if self.name == 'avg':
			return relation.AvgFactory(self.argument.compile(column_mappings))
		raise ValueError('Unknown aggregation function %r' % self.name)

class BinaryOperationNode(ExpressionNode):
	def __init__(self, op, lhs, rhs):
		self.op = op
		self.lhs = lhs
		self.rhs = rhs

	def compile(self, env):
		lhs = self.lhs.compile(env)
		rhs = self.rhs.compile(env)
		if self.op == 'and':
			return relation.And(lhs, rhs)
		if self.op == 'or':
			return relation.Or(lhs, rhs)
		if self.op in ['<', '<=', '<>', '!=', '=', '>=', '>']:
			return relation.Comparison(self.op, lhs, rhs)
		if self.op in ['+', '-', '*', '/']:
			return relation.Arithmetic(self.op, lhs, rhs)
		raise ValueError('Unknown binary operator %r' % self.op)

class UnaryOperationNode(ExpressionNode):
	def __init__(self, op, operand):
		self.op = op
		self.operand = operand

	def compile(self, env):
		operand = self.operand.compile(env)
		if self.op == '-':
			return relation.UnaryMinus(operand)
		if self.op == 'not':
			return relation.LogicalNot(operand)
		if self.op == 'is null':
			return relation.IsNull(operand)
		if self.op == 'is not null':
			return relation.IsNotNull(operand)
		raise ValueError('Unknown unary operator %r' % self.op)

class CastNode(ExpressionNode):
	def __init__(self, expression, target_type):
		self.expression = expression
		self.target_type = target_type

	def compile(self, env):
		return relation.Cast(self.expression.compile(env), self.target_type)

CreateTableNode = namedtuple('CreateTableNode', ['name', 'columns'])
InsertIntoNode = namedtuple('InsertIntoNode', ['table_name', 'tuples'])
SelectTableNode = namedtuple('SelectTableNode', ['table', 'alias'])

class ColumnMappings:
	'Maps columns from source tables to columns in the output table'
	def __init__(self):
		self.columns = []

	def add_column(self, table_name, column):
		'''
		Adds a mapping from the column in the source table to the index of the
		column in the environment index.
		'''
		self.columns.append((table_name,
							column.transform(new_index=len(self.columns))))

	def get_column_index(self, column_ref):
		index = None
		for i, (table_name, column) in enumerate(self.columns):
			if column.name != column_ref.column_name:
				continue
			if column_ref.table_name and table_name != column_ref.table_name:
				continue
			if index != None:
				raise ValueError(
						'Column name %r is ambiguous' % column_ref.column_name)
			index = i
		if index == None:
			raise KeyError('Column %r does not exist' % column_ref.column_name)
		return index

	def get_column(self, column_ref):
		'Returns the referenced column from the environment.'
		return self.columns[self.get_column_index(column_ref)][1]

class SelectNode:
	def __init__(self, select_expressions, tables, where_predicate, group_by):
		self.select_expressions = select_expressions
		self.tables = tables
		self.where_predicate = where_predicate
		self.group_by = group_by

	def compile_joins(self, catalog):
		'''
		Returns the result of cross joining all input tables and the mapping of
		source columns to output columns.
		'''
		column_mappings = ColumnMappings()
		table_names = set()
		for table in self.tables:
			table_name = table.alias or table.table
			if table_name in table_names:
				raise ValueError(
					'Non-unique table name or alias %r' % table_name)
			table_names.add(table_name)
			for column in catalog[table.table].columns:
				column_mappings.add_column(table_name, column)

		# Joins
		output_relation = catalog[self.tables[0].table]
		for table in self.tables[1:]:
			output_relation = relation.CrossJoin(
									output_relation, catalog[table.table])
		return output_relation, column_mappings

	def compile_selection(self, input_relation, column_mappings):
		if not self.where_predicate:
			return input_relation
		return relation.Selection(input_relation,
								self.where_predicate.compile(column_mappings))

	def compile_group_by(self, input_relation, column_mappings):
		aggregate_nodes = []

		def extract_aggregates(node):
			'''
			Traverses an expression tree, adding function evaluation nodes to
			the aggregates array.
			'''
			if type(node) == ConstantNode:
				pass
			elif type(node) == ColumnReferenceNode:
				pass
			elif type(node) == FunctionEvaluationNode:
				aggregate_nodes.append(node)
			elif type(node) == BinaryOperationNode:
				extract_aggregates(node.lhs)
				extract_aggregates(node.rhs)
			elif type(node) == UnaryOperationNode:
				extract_aggregates(node.operand)
			elif type(node) == CastNode:
				extract_aggregates(node.expression)
			else:
				raise TypeError('Unrecognized node type %r' % type(node))

		for expression in self.select_expressions:
			extract_aggregates(expression)

		if not (self.group_by or aggregate_nodes):
			return input_relation, column_mappings

		aggregates = [
			node.get_aggregation(column_mappings) for node in aggregate_nodes]
		grouping_columns = []
		output_mappings = ColumnMappings()
		for column_ref in self.group_by:
			table_name, column = column_mappings.columns[
								column_mappings.get_column_index(column_ref)]
			grouping_columns.append(column)
			output_mappings.add_column(table_name, column)

		output_relation = relation.GroupBy(
								input_relation, grouping_columns, aggregates)
		aggregate_columns = output_relation.columns[len(grouping_columns):]
		for node, column in zip(aggregate_nodes, aggregate_columns):
			table_name = None
			# Add aggregates to output mappings
			output_mappings.add_column(table_name, column)
			# Rewrite select list expression to reference output of group by
			node.attribute_access = relation.Attribute(column)
		assert(len(output_relation.columns) == len(grouping_columns) + len(aggregates))

		return output_relation, output_mappings

	def compile_generalized_projection(self, input_relation, column_mappings):
		select_expressions = []
		for expression in self.select_expressions:
			if (type(expression) == ColumnReferenceNode and
				expression.is_wildcard()):
				select_expressions.extend(
					expression.expand_wildcard(column_mappings))
			else:
				select_expressions.append(expression)

		expressions = [expression.compile(column_mappings) for
						expression in select_expressions]
		return relation.GeneralizedProjection(input_relation, expressions)

	def compile(self, catalog):
		stage1, env1 = self.compile_joins(catalog)
		stage2, env2 = self.compile_selection(stage1, env1), env1
		stage3, env3 = self.compile_group_by(stage2, env2)
		return self.compile_generalized_projection(stage3, env3)

class SetOperatorNode:
	operations = {
		'union':relation.Union,
		'intersect':relation.Intersection
	}
	def __init__(self, op, lhs, rhs, distinct):
		self.op = SetOperatorNode.operations[op]
		self.lhs = lhs
		self.rhs = rhs
		self.distinct = distinct

	def compile(self, catalog):
		return self.op(self.lhs.compile(catalog),
					self.rhs.compile(catalog), self.distinct)

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

	def execute(self, sql_command):
		ast_root = parser.parse(sql_command, lexer=lexer)
		statement_type = type(ast_root)
		if statement_type == CreateTableNode:
			self.__execute_create_table(ast_root)
		elif statement_type == InsertIntoNode:
			self.__execute_insert(ast_root)
		elif statement_type == SelectNode or statement_type == SetOperatorNode:
			return ast_root.compile(self.catalog)
		else:
			raise TypeError('Unknown AST node type')

if __name__ == '__main__':
	pass
