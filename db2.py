# types: INTEGER, FLOAT, STRING, BOOLEAN

class Column:
	def __init__(self, name, column_type, nullable=True):
		self.name = name
		self.type = column_type
		self.nullable = nullable

class Relation:
	def __init__(self, columns, name=None):
		self.name = name
		self.columns = columns

	def set_name(self, name):
		self.name = name

	def __iter__(self):
		'Returns an iterator for iterating over all tuples in the relation'
		raise NotImplemented

	# TODO: materialize - have base relation provide support for free?

class BaseRelation(Relation):
	'''
	A base relation stores a list of tuples. All other relations are derived
	from other relations.
	'''
	def __init__(self, columns, name):
		super().__init__(columns, name)
		self.rows = []

	def insert_row(self, values):
		# TODO: validate types
		pass

	def __iter__(self):
		return self.row.__iter__()

class Expression:
	def value_type(self):
		'''Returns the type the expression evaluates to'''
		raise NotImplemented

# TODO:
# Expression:
# eval(tuple) -> <result type>
# - optional name
#
# - NULL in arithmetic
# - x + NULL = NULL
# - TRUE AND NULL = NULL
# - TRUE OR NULL = TRUE
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
# - sort key
# - sort order

class Selection(Relation):
	def __init__(self, relation, predicate):
		'''
		Represents all tuples in the relation meeting the predicate.
		The derived relation is optionally given a name.
		'''
		super().__init__(relation.columns)

class GeneralizedProjection(Relation):
	def __init__(self, relation, expressions, distinct=False):
		'''
		Represents a relation where each tuple's attributes are expressions in
		terms of the input tuple attributes. There is an output tuple for each
		input tuple unless distinct is true in which case duplicate output
		tuples are omitted.
		'''
		pass

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

class Union(Relation):
	def __init__(self, relations, distinct=True):
		'''
		Represents a relation including all the tuples of the input relations.

		The input relations must have the same number of columns and the columns
		must have the same types.

		If distinct is true, duplicate tuples are omitted.
		'''
		# TODO: validate input, put in function to share with Intersection and
		# Difference
		columns = []
		for column in relations[0].columns:
			new_name = renamings.get(column.name, column.name)
			columns.append(Column(new_name, column.type, column.nullable))
		super().__init__(columns)

class Intersection(Relation):
	def __init__(self, relations, distinct=True):
		'''
		Represents a relation consisting of only the tuples present in all the
		input relations.

		The input relations must have the same number of columns and the columns
		must have the same types.

		If distinct is true, duplicate tuples are omitted.
		'''
		pass

class Difference(Relation):
	def __init__(self, lhs_relation, rhs_relation, distinct=True):
		'''
		Represents a relation consisting of tuples present in the left relation
		but not the right relation.

		The input relations must have the same number of columns and the columns
		must have the same types.

		If distinct is true, duplicate tuples are omitted.
		'''
		pass

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

# LeftOuterJoin
# RightOuterJoin
# FullOuterJoin
