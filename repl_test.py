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

	# TODO: select column by fully qualified name
	# table alias
	#	alias has same name as table
	#	alias defined multiple times
	# column alias
	# select all vs select distinct
	# order by asc, desc, nulls first, last

# Insert into
# TODO: use integer literal for floating point column

if __name__ == '__main__':
	unittest.main()