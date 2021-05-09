#!/usr/bin/env python3

from repl import *
import unittest

class TestCreateTable(unittest.TestCase):

	# TODO: split into - has correct column names, parses types, parses
 	# nullability
	def test(self):
		db = Db()
		db.execute('''CREATE TABLE Pets (
					Name STRING NOT NULL,
					Age INTEGER,
					Weight FLOAT,
					FavoriteFood STRING NULL,
					IsReptile BOOLEAN
					);''')

		self.assertTrue('pets' in db.catalog)
		self.assertEqual(db.catalog['pets'].name, 'pets')
		self.assertEqual(len(db.catalog['pets'].columns), 5)
		columns = db.catalog['pets'].columns
		self.assertEqual(columns[0].name, 'name')
		self.assertEqual(columns[0].type, str)
		self.assertEqual(columns[0].nullable, False)
		self.assertEqual(columns[0].index, 0)
		self.assertEqual(columns[1].name, 'age')
		self.assertEqual(columns[1].type, int)
		self.assertEqual(columns[1].nullable, True)
		self.assertEqual(columns[1].index, 1)
		self.assertEqual(columns[2].name, 'weight')
		self.assertEqual(columns[2].type, float)
		self.assertEqual(columns[2].nullable, True)
		self.assertEqual(columns[2].index, 2)
		self.assertEqual(columns[3].name, 'favoritefood')
		self.assertEqual(columns[3].type, str)
		self.assertEqual(columns[3].nullable, True)
		self.assertEqual(columns[3].index, 3)
		self.assertEqual(columns[4].name, 'isreptile')
		self.assertEqual(columns[4].type, bool)
		self.assertEqual(columns[4].nullable, True)
		self.assertEqual(columns[4].index, 4)

	def test_should_return_error_for_invalid_schema(self):
		db = Db()
		test_cases = [
			('create yolo ( name string, age integer);', 'invalid entity'),
			('create table  name string, age integer);', 'missing open paren'),
			('create table ( name string, age integer;', 'missing close paren'),
			('create table ();', 'empty schema'),
			('create table ( string, age integer);', 'missing column name'),
			('create table ( 123 string, age integer);', 'invalid column name'),
			('create table ( name yolo, age integer);', 'invalid column type'),
			('create table ( name string not);', 'invalid nullability'),
			('create table ( name string null ish);', 'invalid nullability'),
			('create table ( name string age integer);', 'missing comma')
		]
		for statement, description in test_cases:
			with self.assertRaisesRegex(ValueError, 'Syntax', msg=description):
				db.execute(statement)

class TestInsertInto(unittest.TestCase):

	def test(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float, d boolean);')
		db.execute('''insert into t VALUES (
				(123, \'abc\', 3.14, true),
				(456, \'def\', 2.71, false)
				);''')

		self.assertEqual(list(db.catalog['t']), [
				(123, 'abc', 3.14, True),
				(456, 'def', 2.71, False),
			])

	def test_should_insert_nulls_for_nullable_column(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float, d boolean);')
		db.execute('insert into t VALUES ((null, null, null, null));')

		self.assertEqual(list(db.catalog['t']), [
				(None, None, None, None)
			])

	def test_should_raise_error_for_invalid_type(self):
		db = Db()
		db.execute('create table t (a integer, b string);')

		with self.assertRaisesRegex(TypeError, 'wrong type'):
			db.execute('insert into t VALUES ((\'hi\', true));')

	def test_should_raise_error_inserting_null_value_in_not_null_field(self):
		db = Db()
		db.execute('create table t (a integer not null, b string);')

		with self.assertRaisesRegex(TypeError, 'NULL value'):
			db.execute('insert into t values ((null, \'hi\'));')

	def test_should_raise_error_for_non_existing_table(self):
		db = Db()
		with self.assertRaisesRegex(KeyError, 'Table .* does not exist'):
			db.execute('insert into dne values ((123, \'hi\'));')

	def test_should_raise_error_for_wrong_number_of_fields(self):
		db = Db()
		db.execute('create table t (a integer, b string);')

		with self.assertRaisesRegex(TypeError, 'number of columns'):
			db.execute('insert into t values ((123, \'hi\', true));')

	def test_should_raise_error_for_invalid_syntax(self):
		db = Db()
		test_cases = [
			('insert into t values (123, \'hi\', true);',
			 'invalid tuple list'),
			('into t values ((1,2), (3,4));',
			 'missing insert'),
			('insert t values ((1,2), (3,4));',
			 'missing into'),
			('insert into 123 values ((1,2), (3,4));',
			 'invalid name'),
			('insert into t value ((1,2), (3,4));',
			 'missing values'),
			('insert into t values ((1,2),));',
			 'trailing comma invalid list'),
			('insert into t values ((1,2) (3,4));',
			 'missing comma'),
			('insert into t values ((1,2), (3,4))',
			 'missing semicolon'),
			('insert into t values ((1,), (3,4));',
			 'invalid tuple')
		]
		for command, msg in test_cases:
			with self.assertRaisesRegex(ValueError, 'Syntax', msg=msg):
				db.execute(command)

	def test_insert_should_be_atomic(self):
		db = Db()
		db.execute('create table t (a integer not null, b string);')
		db.execute('insert into t values ((1, \'a\'), (2, \'b\'));')

		# The valid tuple (3, 'c') should not be inserted because the other
		# tuple (null, 'd') violates the not null constraint.
		with self.assertRaisesRegex(TypeError, 'NULL value'):
			db.execute('insert into t values ((3, \'c\'), (null, \'d\'));')

		self.assertEqual(list(db.catalog['t']), [(1, 'a'), (2, 'b')])

class TestSelect(unittest.TestCase):

	def test_select_all_columns(self):
		db = Db()
		db.execute('create table t (a integer, b string);')
		db.execute('insert into t values ((1, \'a\'), (2, \'b\'));')

		cursor = db.execute('select * from t;')

		self.assertEqual(list(cursor), [(1, 'a'), (2, 'b')])

	def test_should_raise_error_if_table_does_not_exist(self):
		db = Db()
		with self.assertRaisesRegex(KeyError, 'dne'):
			db.execute('select * from dne;')

	def test_select_columns_by_name(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')
		db.execute('insert into t values ((1, \'a\', 3.14), (2, \'b\', 2.71));')

		cursor = db.execute('select a, c from t;')

		self.assertEqual(list(cursor), [(1, 3.14), (2, 2.71)])

	def test_should_raise_error_if_column_does_not_exist(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')

		with self.assertRaisesRegex(KeyError, 'dne'):
			db.execute('select dne from t;')

	def test_select_columns_by_full_name(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')
		db.execute('insert into t values ((1, \'a\', 3.14), (2, \'b\', 2.71));')

		cursor = db.execute('select t.a, t.c from t;')

		self.assertEqual(list(cursor), [(1, 3.14), (2, 2.71)])

	def test_select_table_alias(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')
		db.execute('insert into t values ((1, \'a\', 3.14), (2, \'b\', 2.71));')

		cursor = db.execute('select s.a, c from t as s;')

		self.assertEqual(list(cursor), [(1, 3.14), (2, 2.71)])

	def test_select_table_short_alias(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')
		db.execute('insert into t values ((1, \'a\', 3.14), (2, \'b\', 2.71));')

		cursor = db.execute('select s.a, c from t s;')

		self.assertEqual(list(cursor), [(1, 3.14), (2, 2.71)])

	def test_select_should_raise_error_for_reference_to_original_table(self):
		db = Db()
		db.execute('create table t (a integer, b string, c float);')

		with self.assertRaisesRegex(KeyError, 't'):
			cursor = db.execute('select t.a from t as s;')

	def test_select_constant(self):
		db = Db()
		db.execute('create table t (a integer, b string);')
		db.execute('insert into t values ((1, \'a\'), (2, \'b\'));')

		cursor = db.execute('select 123, 3.14, \'hi\', true, null from t;')

		# Number of tuples should equal number of tuples in input table
		self.assertEqual(list(cursor), [
			(123, 3.14, 'hi', True, None),
			(123, 3.14, 'hi', True, None)
		])

	def test_select_expression_with_binary_operation(self):
		db = Db()
		db.execute('create table t (a integer);')
		db.execute('insert into t values ((10), (15), (20));')

		cursor = db.execute('''
			select
				a + 1,
				a - 1,
				a * 2,
				a / 2,
				a < 15,
				a <= 15,
				a = 15,
				a <> 15,
				a != 15,
				a >= 15,
				a > 15
			from t;''')

		# Number of tuples should equal number of tuples in input table
		self.assertEqual(list(cursor), [
			(11, 9, 20, 5, True, True, False, True, True, False, False),
			(16, 14, 30, 7, False, True, True, False, False, True, False),
			(21, 19, 40, 10, False, False, False, True, True, True, True)
		])

	def test_select_expression_with_and_or(self):
		db = Db()
		db.execute('create table t (a boolean);')
		db.execute('insert into t values ((true), (false));')

		cursor = db.execute('''
			select
				a AND true,
				a AND false,
				a OR true,
				a OR false
			from t;''')

		# Number of tuples should equal number of tuples in input table
		self.assertEqual(list(cursor), [
			(True, False, True, True),
			(False, False, True, False)
		])

	def test_select_expression_unary_minus(self):
		db = Db()
		db.execute('create table t (a integer);')
		db.execute('insert into t values ((10), (15), (20));')

		cursor = db.execute('''select -a from t;''')

		self.assertEqual(list(cursor), [ (-10,), (-15,), (-20,) ])

	def test_select_expression_logical_not(self):
		db = Db()
		db.execute('create table t (a boolean);')
		db.execute('insert into t values ((true), (false));')

		cursor = db.execute('''select not a from t;''')

		self.assertEqual(list(cursor), [(False,), (True,)])

	def test_select_expression_is_null(self):
		db = Db()
		db.execute('create table t (a integer);')
		db.execute('insert into t values ((10), (null));')

		cursor = db.execute('''select a is null, a is not null from t;''')

		self.assertEqual(list(cursor), [(False, True), (True, False)])

	def test_cast_from_boolean(self):
		db = Db()
		db.execute('create table t (a boolean);')
		db.execute('insert into t values ((true), (false));')

		cursor = db.execute(
					'select cast(a as integer), cast(a as string) from t;')

		self.assertEqual(list(cursor), [(1, 'true'), (0, 'false')])

	def test_should_raise_error_casting_boolean_to_float(self):
		db = Db()
		db.execute('create table t (a boolean);')
		db.execute('insert into t values ((true), (false));')

		with self.assertRaisesRegex(TypeError, 'cast'):
			cursor = db.execute('select cast(a as float) from t;')

	def test_cast_from_integer(self):
		db = Db()
		db.execute('create table t (a integer);')
		db.execute('insert into t values ((0), (10));')

		cursor = db.execute('''select
									cast(a as boolean),
									cast(a as float),
									cast(a as string)
								from t;''')

		self.assertEqual(list(cursor), [(False, 0.0, '0'), (True, 10.0, '10')])

	def test_cast_from_float(self):
		db = Db()
		db.execute('create table t (a float);')
		db.execute('insert into t values ((3.14));')

		cursor = db.execute('''select
									cast(a as integer),
									cast(a as string)
								from t;''')

		self.assertEqual(list(cursor), [(3, '3.14')])

	def test_should_raise_error_casting_float_to_boolean(self):
		db = Db()
		db.execute('create table t (a float);')
		db.execute('insert into t values ((3.14));')

		with self.assertRaisesRegex(TypeError, 'cast'):
			cursor = db.execute('select cast(a as boolean) from t;')
	# TODO: cast from string

	# TODO: complex expression - precedence test
	# TODO: invalid expressions
	# 	- missing operator, missing operand
	#	- incorrect types
		
	def test_where_clause(self):
		db = Db()
		db.execute('create table t (a integer, b string);')
		db.execute('''insert into t values (
			(123, \'hi\'),
			(456, \'bye\'),
			(789, \'hi\')
			);''')

		cursor = db.execute('select a from t where b = \'hi\';')

		# Number of tuples should equal number of tuples in input table
		self.assertEqual(list(cursor), [
			(123,), (789,)
		])

	def test_should_raise_error_for_where_clause_missing_predicate(self):
		db = Db()
		with self.assertRaisesRegex(ValueError, 'Syntax'):
			db.execute('select a from t where ;')

	def test_should_raise_error_for_non_boolean_where_expression(self):
		db = Db()
		db.execute('create table t (a integer, b string);')
		with self.assertRaisesRegex(TypeError, 'must be a boolean'):
			db.execute('select a from t where 123;')

	def test_cross_join(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b integer);')
		db.execute('insert into r values ((0), (10));')
		db.execute('insert into s values ((1), (2));')

		cursor = db.execute('select a, b from r, s;')

		self.assertEqual(list(cursor), [(0, 1), (0, 2), (10, 1), (10, 2)])

	def test_cross_join_wildcard(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b integer);')
		db.execute('insert into r values ((0), (10));')
		db.execute('insert into s values ((1), (2));')

		cursor = db.execute('select * from r, s;')

		self.assertEqual(list(cursor), [(0, 1), (0, 2), (10, 1), (10, 2)])

	# TODO:
	# def test_cross_join_with_table_wildcard(self):
	# 	db = Db()
	# 	db.execute('create table r (a integer);')
	# 	db.execute('create table s (b integer, c integer);')
	# 	db.execute('insert into r values ((0), (10));')
	# 	db.execute('insert into s values ((1, 11), (2, 22);')

	# 	cursor = db.execute('select a, s.* from r, s;')

	# 	self.assertEqual(list(cursor), [
	# 		(0, 1, 11), (0, 2, 22), (10, 1, 11), (10, 2, 22)])

	def test_join_with_predicate(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b integer);')
		db.execute('insert into r values ((0), (4), (10));')
		db.execute('insert into s values ((1), (5));')

		cursor = db.execute('select a, b from r, s where b > a;')

		self.assertEqual(list(cursor), [(0, 1), (0, 5), (4, 5)])

	def test_join_with_many_tables(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b boolean);')
		db.execute('create table t (c string);')
		db.execute('insert into r values ((0), (1));')
		db.execute('insert into s values ((true), (false));')
		db.execute('''insert into t values (('a'), ('b'));''')

		cursor = db.execute('select a, b, c from r, s, t;')

		self.assertEqual(list(cursor), [(0, True, 'a'), (0, True, 'b'),
			(0, False, 'a'), (0, False, 'b'), (1, True, 'a'), (1, True, 'b'),
			(1, False, 'a'), (1, False, 'b')])

	def test_should_raise_error_for_abigous_column_name(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (a integer);')

		with self.assertRaisesRegex(ValueError, 'ambiguous'):
			db.execute('select a from r, s;')

	def test_join_multiple_tables_with_same_column_name(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (a integer);')
		db.execute('insert into r values ((0), (10));')
		db.execute('insert into s values ((1), (2));')

		cursor = db.execute('select r.a, s.a from r, s;')

		self.assertEqual(list(cursor), [(0, 1), (0, 2), (10, 1), (10, 2)])

	def test_should_raise_error_for_non_unique_table_name_and_alias(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b integer);')

		with self.assertRaisesRegex(ValueError, 'Non-unique table name'):
			db.execute('select * from r, s as r;')

	def test_should_raise_error_for_non_unique_alias(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (b integer);')

		with self.assertRaisesRegex(ValueError, 'Non-unique table name'):
			db.execute('select * from r t, s as t;')

	def test_table_alias_has_same_name_as_exisitng_table(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('create table s (a integer);')
		db.execute('insert into r values ((0), (10));')
		db.execute('insert into s values ((1), (2));')

		cursor = db.execute('select s.a from r as s;')

		self.assertEqual(list(cursor), [(0,), (10,)])

	def test_join_table_with_self(self):
		db = Db()
		db.execute('create table r (a integer);')
		db.execute('insert into r values ((1), (2));')

		cursor = db.execute('select r.a, s.a from r, r as s;')

		self.assertEqual(list(cursor), [(1, 1), (1, 2), (2, 1), (2, 2)])

	def test_should_raise_error_for_select_with_nonaggregated_column(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')

		# TODO: Improve the error message
		with self.assertRaisesRegex(KeyError, 'a'):
			db.execute('select a from t group by b;')

	def test_group_by_no_aggregates(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 31), (3, 32));')

		cursor = db.execute('select a from t group by a;')

		self.assertEqual(list(cursor), [(1,), (3,)])

	def test_group_by_multiple_columns(self):
		db = Db()
		db.execute('create table t (a integer, b integer, c integer);')
		db.execute('''insert into t values (
				(1, 11, 1),
				(1, 11, 2),
				(1, 11, 3),
				(3, 31, 1),
				(3, 32, 1),
				(3, 32, 2)
		);''')

		cursor = db.execute('select a, b, a + b from t group by a, b;')

		self.assertEqual(list(cursor), [(1,11, 12), (3,31, 34), (3,32, 35)])

	def test_group_by_with_where_clause_referencing_group_by_column(self):
		db = Db()
		db.execute('create table t (a integer, b integer, c integer);')
		db.execute('''insert into t values (
				(1, 11, 1),
				(1, 11, 2),
				(1, 11, 3),
				(3, 31, 1),
				(3, 32, 1),
				(3, 32, 2)
		);''')

		cursor = db.execute('select b from t where a = 3 group by a, b;')

		self.assertEqual(list(cursor), [(31,), (32,)])

	def test_group_by_with_where_clause_referencing_non_aggregated_column(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('''insert into t values (
				(1, 1),
				(1, 2),
				(1, 3),
				(2, 2),
				(2, 4),
				(3, 1),
				(3, 1),
				(3, 2)
		);''')

		cursor = db.execute('select a from t where b = 1 group by a;')

		self.assertEqual(list(cursor), [(1,), (3,)])

	def test_should_raise_error_for_nonaggregated_column_implicit_group(self):
		db = Db()
		db.execute('create table t (a integer);')

		# TODO: Improve the error message
		with self.assertRaisesRegex(KeyError, 'a'):
			db.execute('select a + count(1) from t;')

	def test_aggregation_with_implicit_group_by(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 31), (3, 32));')

		cursor = db.execute('select min(a) + max(b), 10*count(1) from t;')

		self.assertEqual(list(cursor), [(33, 40)])

	def test_group_by(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 31), (3, 32));')

		cursor = db.execute('''select
				a, max(b), min(b), count(b), avg(b), sum(b)
			from t group by a;''')

		self.assertEqual(list(cursor),
			[(1, 12, 11, 2, 11.5, 23), (3, 32, 31, 2, 31.5, 63)])

	def test_aggregation_of_group_by_column(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 31), (3, 32));')

		cursor = db.execute('''select
				a, max(a), min(a), count(a), avg(a), sum(a)
			from t group by a;''')

		self.assertEqual(list(cursor),
			[(1, 1, 1, 2, 1, 2), (3, 3, 3, 2, 3, 6)])

	def test_aggregation_of_expression(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 31), (3, 32));')

		cursor = db.execute('select a, max(2*b) from t group by a;')

		self.assertEqual(list(cursor), [(1, 24), (3, 64)])

	def test_expression_of_aggregations(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('insert into t values ((1, 11), (1, 12), (3, 30), (3, 32));')

		cursor = db.execute('''select
				10*a,  max(b) - min(b), count(a) + sum(a)
			from t group by a;''')

		self.assertEqual(list(cursor), [(10, 1, 4), (30, 2, 8)])

	def test_group_by_and_where(self):
		db = Db()
		db.execute('create table t (a integer, b integer);')
		db.execute('''insert into t values (
			(1, 10), (1, 20), (3, 30), (3, 40), (4, 50));''')

		cursor = db.execute('select a,  max(b) from t where b < 35 group by a;')

		self.assertEqual(list(cursor), [(1, 20), (3, 30)])

	# TODO:
	# - table wildcard e.g. SELECT r.* FROM r, s
	# TODO:
	# column alias
	# select all vs select distinct
	# order by asc, desc, nulls first, last
	# select without a "FROM" e.g. "select 123;"

# Insert into
# TODO: use integer literal for floating point column

if __name__ == '__main__':
	unittest.main()
