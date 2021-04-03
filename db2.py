import itertools

# types: INTEGER, FLOAT, STRING, BOOLEAN

class Column:
	def __init__(self, name, column_type, nullable=True, index=None):
		self.name = name
		self.type = column_type
		self.nullable = nullable
		self.index = index

	def check_value_type(self, value):
		'Raise a TypeError exception if value has the wrong type'
		if type(value) == type(None):
			if self.nullable:
				return
			raise TypeError('Cannot use NULL value for column %s' % self.name)
		if type(value) != self.type:
			raise TypeError('Value %r of type %r is wrong type for column %s' %
				(value, type(value), self.type))

	def transform(self, new_name=None, new_column_type=None,
			new_nullability=None, new_index=None):
		'''
		Returns a new column identical to the original except for the specified
		fields
		'''
		return Column(new_name or self.name,
				new_column_type or self.type,
				new_nullability if new_nullability != None else self.nullable,
				new_index if new_index != None else self.index)

class Relation:
	def __init__(self, columns, name=None):
		self.name = name
		self.columns = [
			column.transform(new_index=i) for i, column in enumerate(columns)]

	def set_name(self, name):
		self.name = name

	def __iter__(self):
		'Returns an iterator for iterating over all tuples in the relation'
		raise NotImplemented

	# TODO: materialize - have base relation provide support for free?
	# or have relations automatically swapped out for material relations after
	# first iteration

class MaterialRelation(Relation):
	'''
	A material relation stores a list of tuples. All other relations are derived
	from other relations.
	'''
	def __init__(self, columns, name=None):
		super().__init__(columns, name)
		self.rows = []

	def insert(self, values):
		if len(values) != len(self.columns):
			raise TypeError("Wrong number of columns")
		for value, column in zip(values, self.columns):
			column.check_value_type(value)
		self.rows.append(tuple(values))

	def __iter__(self):
		return self.rows.__iter__()

class Expression:
	def value_type(self):
		'Returns the type the expression evaluates to'
		raise NotImplemented

	def nullable(self):
		'Returns true if the expression can evaluate to a null value'
		raise NotImplemented

	def evaluate(self, row):
		'Returns the value of the expression for the attribute values of a row'
		raise NotImplemented

class Constant(Expression):
	def __init__(self, value):
		self.value = value

	def value_type(self):
		return type(self.value)

	def nullable(self):
		return self.value == None

	def evaluate(self, row):
		return self.value

class Attribute(Expression):
	def __init__(self, column):
		self.column = column

	def value_type(self):
		return self.column.type

	def nullable(self):
		return self.column.nullable

	def evaluate(self, row):
		value = row[self.column.index]
		self.column.check_value_type(value) # remove later
		return value

def str_to_bool(s):
	if s == None:
		return None
	s = s.lower()
	if s == 'true' or s == '1':
		return True
	if s == 'false' or s == '0':
		return False
	raise TypeError('String %r is an invalid boolean' % s)

def str_to_int(s):
	if s == None:
		return None
	if s.startswith('-') and s[1:].isdigit() or s.isdigit():
		return int(s)
	raise TypeError('String %r is an invalid integer' % s)

def str_to_float(s):
	if s == None:
		return None
	try:
		return float(s)
	except:
		raise TypeError('String %r is an invalid float' % s)

class Cast(Expression):
	conversion_functions = {
		# TODO: raise error for casting type T to type T
		bool: {
			bool: lambda x: x,
			int: lambda x: int(x) if x != None else None,
			float: TypeError('Cannot cast BOOLEAN to FLOAT'),
			str: lambda x: {None:None, True:'true', False:'false'}[x]
		},
		int: {
			bool: lambda x: x != 0 if x != None else None,
			int: lambda x: x,
			float: lambda x: float(x) if x != None else None,
			str: lambda x: str(x) if x != None else None,
		},
		float: {
			bool: TypeError('Cannot cast FLOAT to BOOLEAN'),
			int: lambda x: int(x) if x != None else None,
			float: lambda x: x,
			str: lambda x: str(x) if x != None else None,
		},
		str: {
			bool: str_to_bool,
			int: str_to_int,
			float: str_to_float,
			str: lambda x: x,
		},
	}
	def __init__(self, expression, target_type):
		self.op = (
			Cast.conversion_functions[expression.value_type()][target_type])
		if isinstance(self.op, TypeError):
			raise self.op
		self.expression = expression

	def value_type(self):
		return target_type

	def nullable(self):
		return self.expression.nullable()

	def evaluate(self, row):
		if row == None:
			return None
		return self.op(self.expression.evaluate(row))

class BinaryOperation(Expression):
	def __init__(self, lhs, rhs):
		self.lhs = lhs
		self.rhs = rhs

	def nullable(self):
		return self.lhs.nullable() or self.rhs.nullable()

	def evaluate(self, row):
		lhs = self.lhs.evaluate(row)
		if lhs == None:
			return None
		rhs = self.rhs.evaluate(row)
		if rhs == None:
			return None
		return self.op(lhs, rhs)

class And(BinaryOperation):
	def __init__(self, lhs, rhs):
		super().__init__(lhs, rhs)
		if lhs.value_type() != bool or rhs.value_type() != bool:
			raise TypeError('Operands of and must be booleans')

	def value_type(self):
		return bool

	def evaluate(self, row):
		lhs = self.lhs.evaluate(row)
		if lhs == False:
			return False
		if lhs == True:
			return self.rhs.evaluate(row)
		if self.rhs.evaluate(row) == False:
			return False
		return None

class Or(BinaryOperation):
	def __init__(self, lhs, rhs):
		super().__init__(lhs, rhs)
		if lhs.value_type() != bool or rhs.value_type() != bool:
			raise TypeError('Operands of or must be booleans')

	def value_type(self):
		return bool

	def evaluate(self, row):
		lhs = self.lhs.evaluate(row)
		if lhs == True:
			return True
		if lhs == False:
			return self.rhs.evaluate(row)
		if self.rhs.evaluate(row):
			return True
		return None

class Comparison(BinaryOperation):
	operators = {
		'<': lambda a, b: a < b,
		'<=': lambda a, b: a <= b,
		'=': lambda a, b: a == b,
		'>=': lambda a, b: a >= b,
		'>': lambda a, b: a > b,
		'<>': lambda a, b: a != b,
	}
	def __init__(self, op, lhs, rhs):
		super().__init__(lhs, rhs)
		if lhs.value_type() != rhs.value_type():
			raise TypeError('Operands must have the same type')
		# TODO: compare int and float
		self.op = Comparison.operators[op]

	def value_type(self):
		return bool

def is_numeric(value_type):
	return value_type == int or value_type == float

class Arithmetic(BinaryOperation):
	operators = {
		'*': lambda a, b: a * b,
		'/': lambda a, b: a / b,
		'//': lambda a, b: a // b,
		'%': lambda a, b: a % b,
		'+': lambda a, b: a + b,
		'-': lambda a, b: a - b,
	}
	def __init__(self, op, lhs, rhs):
		super().__init__(lhs, rhs)

		if not (is_numeric(lhs.value_type()) and is_numeric(rhs.value_type())):
			raise TypeError('Operands to %r must be numeric' % op)
		self.type = float if (lhs.value_type() == float or
								rhs.value_type() == float) else int
		if op == '/' and self.type == int:
			op = '//'
		self.op = Arithmetic.operators[op]

	def value_type(self):
		return self.type

class UnaryMinus(Expression):
	def __init__(self, expression):
		if not is_numeric(expression.value_type()):
			raise TypeError('Operands to minus must be numeric')
		self.expression = expression

	def value_type(self):
		return self.expression.value_type()

	def nullable(self):
		return self.expression.nullable()

	def evaluate(self, row):
		value = self.expression.evaluate(row)
		if value == None:
			return None
		return - value

class LogicalNot(Expression):
	def __init__(self, expression):
		if expression.value_type() != bool:
			raise TypeError('Operands to logical not must be boolean')
		self.expression = expression

	def value_type(self):
		return bool

	def nullable(self):
		return self.expression.nullable()

	def evaluate(self, row):
		value = self.expression.evaluate(row)
		if value == None:
			return None
		return not value

class IsNull(Expression):
	def __init__(self, expression):
		self.expression = expression

	def value_type(self):
		return bool

	def nullable(self):
		return False

	def evaluate(self, row):
		return self.expression.evaluate(row) == None

class IsNotNull(Expression):
	def __init__(self, expression):
		self.expression = expression

	def value_type(self):
		return bool

	def nullable(self):
		return False

	def evaluate(self, row):
		return self.expression.evaluate(row) != None

class Selection(Relation):
	def __init__(self, relation, predicate):
		'''
		Represents all tuples in the relation meeting the predicate.
		The derived relation is optionally given a name.
		'''
		super().__init__(relation.columns)
		if predicate.value_type() != bool:
			raise TypeError('Predicate must be a boolean valued expression')
		self.relation = relation
		self.predicate = predicate

	def __iter__(self):
		return (row for row in self.relation if self.predicate.evaluate(row))


class Deduplicate(Relation):
	def __init__(self, relation):
		'''
		Represents a relation with all duplicate tuples removed.
		'''

# TODO: name columns in output
class GeneralizedProjection(Relation):
	def __init__(self, relation, expressions):
		'''
		Represents a relation where each tuple's attributes are expressions in
		terms of the input tuple attributes. There is an output tuple for each
		input tuple.
		'''
		columns = []
		for expression in expressions:
			# TODO: Infer name when possible (e.g. When expression is an
			# attribute, reuse the attribute name)
			column = Column(None,expression.value_type(), expression.nullable())
			columns.append(column)
		super().__init__(columns)
		self.relation = relation
		self.expressions = expressions

	def __iter__(self):
		project = lambda row: tuple([x.evaluate(row) for x in self.expressions])
		return (project(row) for row in self.relation)

class Sort(MaterialRelation):
	def __init__(self, relation, sort_key=None, descending=False):
		super().__init__(relation.columns)
		self.relation = relation
		self.sort_key = None
		if sort_key:
			for column in sort_key:
				if column not in relation.columns:
					raise ValueError(
					'Sort key %r is not a column of the relation' % column.name)
			self.sort_key = lambda row: [
				row[column.index] for column in sort_key]
		self.descending = descending
		self.materialized = False

	def __iter__(self):
		if not self.materialized:
			self.rows = list(self.relation)
			self.rows.sort(key=self.sort_key, reverse=self.descending)
		return self.rows.__iter__()

def create_compatible_schema(lhs_relation, rhs_relation):
	'''
	Returns a schema compatible with both relations.

	The names of the columns in the returned schema are the same as the names of
	the lhs relation and a column is nullable if either of the corresponding
	input columns are nullable.

	The relations must have the same number of columns and they must have the
	same data types.
	'''
	if len(lhs_relation.columns) != len(rhs_relation.columns):
		raise ValueError('Relations must have the same number of columns')
	columns = [column.transform() for column in lhs_relation.columns]
	for i in range(len(lhs_relation.columns)):
		lhs_column = lhs_relation.columns[i]
		rhs_column = rhs_relation.columns[i]
		if lhs_column.type != rhs_column.type:
			raise ValueError('Relations must have the same column types')
		columns[i].nullable = lhs_column.nullable or rhs_column.nullable
	return columns

def next_value(iterator):
	'Returns the next value from the iterator or None.'
	try:
		return iterator.__next__()
	except StopIteration:
		return None

def remove_duplicates(iterator):
	'Produces iterator elements with consecutive duplicate elements removed.'
	current = next_value(iterator)
	while current:
		yield current
		value = next_value(iterator)
		while value == current:
			value = next_value(iterator)
		current = value

def stream_union(lhs_iter, rhs_iter):
	'''
	Returns a sorted stream with all values - including duplicates - from two
	sorted input streams.

	The input streams must be in ascending order.
	'''
	lhs = next_value(lhs_iter)
	rhs = next_value(rhs_iter)
	while lhs and rhs:
		if lhs <= rhs:
			yield lhs
			lhs = next_value(lhs_iter)
		else:
			yield rhs
			rhs = next_value(rhs_iter)
	while lhs:
		yield lhs
		lhs = next_value(lhs_iter)
	while rhs:
		yield rhs
		rhs = next_value(rhs_iter)

def stream_intersection(lhs_iter, rhs_iter):
	'''
	Returns a sorted stream with all values - including duplicates - which
	appear in both of the sorted input streams.

	The input streams must be in ascending order.
	'''
	lhs = next_value(lhs_iter)
	rhs = next_value(rhs_iter)
	while lhs and rhs:
		if lhs < rhs:
			lhs = next_value(lhs_iter)
			continue
		if lhs > rhs:
			rhs = next_value(rhs_iter)
			continue
		value = lhs
		while lhs == value:
			yield lhs
			lhs = next_value(lhs_iter)
		while rhs == value:
			yield rhs
			rhs = next_value(rhs_iter)

def stream_difference(lhs_iter, rhs_iter):
	'''
	Returns a sorted stream with all values - including duplicates - which occur
	in the lhs sorted input stream, but not the rhs stream.

	The input streams must be in ascending order.
	'''
	lhs = next_value(lhs_iter)
	rhs = next_value(rhs_iter)
	while lhs and rhs:
		if lhs < rhs:
			value = lhs
			while lhs == value:
				yield lhs
				lhs = next_value(lhs_iter)
		elif lhs == rhs:
			value = lhs
			while lhs == value:
				lhs = next_value(lhs_iter)
		else:
			rhs = next_value(rhs_iter)
	while lhs:
		yield lhs
		lhs = next_value(lhs_iter)

class SetCombination(Relation):
	def __init__(self, combine_streams, lhs, rhs, distinct=True):
		'''
		Combines the tuples in both input relations by sorting them and passing
		them though a combining function.

		The combination function must accept a stream of sorted values from the
		left and right tuples and output a sorted stream of sorted tuples.

		The input relations must have the same number of columns and the columns
		must have the same types.

		If distinct is true, duplicate tuples are omitted.
		'''
		super().__init__(create_compatible_schema(lhs, rhs))
		self.lhs = Sort(lhs)
		self.rhs = Sort(rhs)
		if distinct:
			self.new_iter = lambda: remove_duplicates(
										combine_streams(self.lhs.__iter__(),
											self.rhs.__iter__()))
		else:
			self.new_iter = lambda: combine_streams(self.lhs.__iter__(),
										self.rhs.__iter__())

	def __iter__(self):
		return self.new_iter()

class Union(SetCombination):
	def __init__(self, lhs, rhs, distinct=True):
		'''
		Represents a relation including all values from both input relations.
		'''
		super().__init__(stream_union, lhs, rhs, distinct)
		# TODO: do not sort and merge for union all

class Intersection(SetCombination):
	def __init__(self, lhs, rhs, distinct=True):
		'''
		Represents a relation consisting of only the tuples present in both
		input relations.
		'''
		super().__init__(stream_intersection, lhs, rhs, distinct)

class Difference(SetCombination):
	def __init__(self, lhs, rhs, distinct=True):
		'''
		Represents a relation consisting of tuples present in the left relation
		but not the right relation.
		'''
		super().__init__(stream_difference, lhs, rhs, distinct)

class GroupBy(Relation):
	def __init__(self, relation, grouping_columns, aggregations=[]):
		'''
		Represents a relation with one output tuple for each distinct set of
		values for the grouping columns in the input relation. Output tuples
		are augmented with aggregations of all tuples sharing the same grouping
		column values.
		'''
		pass

# TODO: Replace with project where expressions handle the rename
# Rename(relation, {'column_1_old_name': 'new_name', ...}
class Rename(Relation):
	def __init__(self, relation, renamings):
		'''
		Renames the columns of relation according to a dictionary mapping input
		column names to output column names.
		'''
		columns = []
		for column in relation.columns:
			new_name = renamings.get(column.name, column.name)
			columns.append(Column(new_name, column.type, column.nullable))
		super().__init__(columns)

def generate_names(n):
	'Returns n auto-generated column names'
	return ['f_%d' for i in range(n)]


class CrossJoin(Relation):
	def __init__(self, relations):
		'''
		Represents a relation consisting of the Cartesian product of the input
		relations.
		'''
		pass

# See: https://postgresql.org/docs/8.3/queries-table-expressions.html#QUERIES-FROM
class InnerJoin(Relation):
	def __init__(self, lhs_relation, rhs_relation, predicate):
		pass

# TODO:
# LeftOuterJoin
# RightOuterJoin
# FullOuterJoin

# - have type and named type classes
# - name normalization
#
# Expression:
# - string: || (concatenation), LIKE (regex match), substring, case transforms
# - x IN <relation>, x NOT IN <relation>
#
# Predicate
# eval(tuple) -> bool
# - special case of expression
#
# Adopt consistent terminology
# - tuple vs row
# - attribute vs column
# - relation vs table
#
# Aggregations
# - initial value
# - update(expression)
# - final
# name() -> string # optional name for the aggregation
#
# Sorting
# - Fancy sort orders... ORDER BY  X ASC, Y DESC, Z DESC
#
# Optimizations
# - not nullible case
#   - evaluation of most expressions is much simpler
#   - IS NULL always false
#   - IS NOT NULL always true
