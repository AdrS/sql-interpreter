#!/usr/bin/env python3

from sql_parser import *
import unittest

class TestCreateTable(unittest.TestCase):

	# TODO: split into - has correct column names, parses types, parses
 	# nullability
	def test(self):
		execute('''CREATE TABLE Pets (
					Name STRING NOT NULL,
					Age INTEGER,
					Weight FLOAT,
					FavoriteFood STRING NULL,
					IsReptile BOOLEAN
					);''')

		self.assertTrue('pets' in catalog)
		self.assertEqual(catalog['pets'].name, 'pets')
		self.assertEqual(len(catalog['pets'].columns), 5)
		columns = catalog['pets'].columns
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
				execute(statement)

class TestInsertInto(unittest.TestCase):
	# TODO: reset catalog before each test

	def test(self):
		execute('create table t (a integer, b string, c float, d boolean);')
		execute('''insert into t VALUES (
				(123, \'abc\', 3.14, true),
				(456, \'def\', 2.71, false)
				);''')

		self.assertEqual(list(catalog['t']), [
				(123, 'abc', 3.14, True),
				(456, 'def', 2.71, False),
			])

	def test_should_insert_nulls_for_nullable_column(self):
		execute('create table t (a integer, b string, c float, d boolean);')
		execute('insert into t VALUES ((null, null, null, null));')

		self.assertEqual(list(catalog['t']), [
				(None, None, None, None)
			])

	def test_should_raise_error_for_invalid_type(self):
		execute('create table t (a integer, b string);')

		with self.assertRaises(TypeError):
			execute('insert into t VALUES ((\'hi\', true));')

	def test_should_raise_error_inserting_null_value_in_not_null_field(self):
		execute('create table t (a integer not null, b string);')

		with self.assertRaises(TypeError):
			execute('insert into t values ((null, \'hi\'));')

	def test_should_raise_error_for_non_existing_table(self):
		with self.assertRaisesRegex(KeyError, 'Table .* does not exist'):
			execute('insert into r values ((123, \'hi\'));')

	def test_should_raise_error_for_wrong_number_of_fields(self):
		execute('create table t (a integer, b string);')

		with self.assertRaisesRegex(TypeError, 'number of columns'):
			execute('insert into t values ((123, \'hi\', true));')

	# TODO: test should not insert any tuples if any are invalid
	# TODO: use integer literal for floating point column
	# TODO: invalid value list e.g. insert into t values (1,2,3);

if __name__ == '__main__':
	unittest.main()
