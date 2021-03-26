#!/usr/bin/env python3

from db2 import *
import unittest

class TestMaterialRelation(unittest.TestCase):

	def test_should_not_insert_wrong_number_of_attributes(self):
		relation = MaterialRelation([Column('uid', int), Column('name', str)])
		with self.assertRaisesRegex(TypeError, 'number of columns'):
			relation.insert([1, 'Alice', 3])

	def test_should_not_insert_value_with_wrong_type(self):
		relation = MaterialRelation([Column('id', int)])
		with self.assertRaisesRegex(TypeError, 'wrong type'):
			relation.insert(['hi'])

	def test_should_not_insert_null_into_not_null_column(self):
		relation = MaterialRelation([Column('id', int, nullable=False)])
		with self.assertRaisesRegex(TypeError, 'NULL'):
			relation.insert([None])

	def test_should_insert_null_into_nullable_column(self):
		relation = MaterialRelation([Column('id', int, nullable=True)])
		relation.insert([None])
		self.assertEqual([(None,)], list(relation))

	def test_should_have_expected_values_after_insert(self):
		relation = MaterialRelation([Column('uid', int), Column('name', str)])
		relation.insert((1, 'Alice'))
		relation.insert((2, 'Bob'))
		relation.insert((3, 'Eve'))

		self.assertEqual([(1, 'Alice'), (2, 'Bob'), (3, 'Eve')], list(relation))

	def test_should_have_expected_name(self):
		relation1 = MaterialRelation([Column('uid', int)], name='Users')
		relation2 = MaterialRelation([Column('uid', int)])
		self.assertEqual(relation1.name, 'Users')
		self.assertEqual(relation2.name, None)
		relation2.set_name('Users')
		self.assertEqual(relation2.name, 'Users')

if __name__ == '__main__':
	unittest.main()
