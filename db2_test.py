#!/usr/bin/env python3

from db2 import *
import unittest

class TestColumn(unittest.TestCase):
	def test_should_have_expected_defaults(self):
		col = Column('Name', str)
		self.assertEqual(col.name, 'Name')
		self.assertEqual(col.type, str)
		self.assertTrue(col.nullable)
		self.assertIsNone(col.index)

	def test_transform_should_replace_fields(self):
		col1 = Column('A', str, nullable=True, index=2)
		col2 = col1.transform(new_name='B', new_column_type=int,
				new_nullability=False, new_index=1)
		self.assertEqual(col2.name, 'B')
		self.assertEqual(col2.type, int)
		self.assertFalse(col2.nullable)
		self.assertEqual(col2.index, 1)

	def test_transform_should_not_modify_original_column(self):
		col1 = Column('A', str, nullable=True, index=2)
		col2 = col1.transform(new_name='B', new_column_type=int,
				new_nullability=False, new_index=1)
		self.assertEqual(col1.name, 'A')
		self.assertEqual(col1.type, str)
		self.assertTrue(col1.nullable)
		self.assertEqual(col1.index, 2)

	def test_transform_should_not_modify_unspecified_fields(self):
		col1 = Column('A', str, nullable=True, index=2)
		col2 = col1.transform()
		self.assertEqual(col1.name, 'A')
		self.assertEqual(col2.type, str)
		self.assertTrue(col2.nullable)
		self.assertEqual(col2.index, 2)

	def test_transform_should_set_zero_values(self):
		col1 = Column('A', str, nullable=True, index=2)
		col2 = col1.transform(new_nullability=False, new_index=0)
		self.assertFalse(col2.nullable)
		self.assertEqual(col2.index, 0)

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

class TestConstantExpression(unittest.TestCase):
	def test_should_have_correct_attributes_for_value(self):
		expr = Constant(123)
		self.assertEqual(expr.value_type(), int)
		self.assertFalse(expr.nullable())
		self.assertEqual(expr.evaluate(('a', 2)), 123)

	def test_should_have_correct_attributes_for_null_value(self):
		expr = Constant(None)
		self.assertEqual(expr.value_type(), type(None))
		self.assertTrue(expr.nullable())
		self.assertEqual(expr.evaluate(('a', 2)), None)

class TestAttributeExpression(unittest.TestCase):
	def test_attributes_should_match_column(self):
		expr = Attribute(Column('uid', int, nullable=True, index=3))
		self.assertEqual(expr.value_type(), int)
		self.assertTrue(expr.nullable())

	def test_evaluate_should_return_error_for_incorrect_row_type(self):
		expr = Attribute(Column('uid', int, index=1))
		with self.assertRaisesRegex(TypeError, 'wrong type for column'):
			expr.evaluate((123, 'hello'))

	def test_should_evaluate_to_expected_value(self):
		expr = Attribute(Column('uid', int, nullable=True, index=1))
		self.assertEqual(expr.evaluate(('Alice', 123)), 123)
		self.assertEqual(expr.evaluate(('Bob', None)), None)

class TestComparison(unittest.TestCase):
	def test_should_non_null_values_should_produce_bool(self):
		cases = [
			('<', 1, 2, True),
			('<', 2, 2, False),
			('<', 2, 1, False),

			('<=', 1, 2, True),
			('<=', 2, 2, True),
			('<=', 2, 1, False),

			('=', 1, 2, False),
			('=', 2, 2, True),
			('=', 2, 1, False),

			('>=', 1, 2, False),
			('>=', 2, 2, True),
			('>=', 2, 1, True),

			('>', 1, 2, False),
			('>', 2, 2, False),
			('>', 2, 1, True),

			('<>', 1, 2, True),
			('<>', 2, 2, False),
			('<>', 2, 1, True),

			('<', 1.1, 2.2, True),
			('<', 2.2, 2.2, False),
			('<', 2.2, 1.1, False),

			('<=', 1.1, 2.2, True),
			('<=', 2.2, 2.2, True),
			('<=', 2.2, 1.1, False),

			('=', 1.1, 2.2, False),
			('=', 2.2, 2.2, True),
			('=', 2.2, 1.1, False),

			('>=', 1.1, 2.2, False),
			('>=', 2.2, 2.2, True),
			('>=', 2.2, 1.1, True),

			('>', 1.1, 2.2, False),
			('>', 2.2, 2.2, False),
			('>', 2.2, 1.1, True),

			('<>', 1.1, 2.2, True),
			('<>', 2.2, 2.2, False),
			('<>', 2.2, 1.1, True),

			('<', False, True, True),
			('<', True, True, False),
			('<', True, False, False),

			('<=', False, True, True),
			('<=', True, True, True),
			('<=', True, False, False),

			('=', False, True, False),
			('=', True, True, True),
			('=', True, False, False),

			('>=', False, True, False),
			('>=', True, True, True),
			('>=', True, False, True),

			('>', False, True, False),
			('>', True, True, False),
			('>', True, False, True),

			('<>', False, True, True),
			('<>', True, True, False),
			('<>', True, False, True),

			('<', 'Alice', 'Bob', True),
			('<', 'Bob', 'Bob', False),
			('<', 'Bob', 'Alice', False),

			('<=', 'Alice', 'Bob', True),
			('<=', 'Bob', 'Bob', True),
			('<=', 'Bob', 'Alice', False),

			('=', 'Alice', 'Bob', False),
			('=', 'Bob', 'Bob', True),
			('=', 'Bob', 'Alice', False),

			('>=', 'Alice', 'Bob', False),
			('>=', 'Bob', 'Bob', True),
			('>=', 'Bob', 'Alice', True),

			('>', 'Alice', 'Bob', False),
			('>', 'Bob', 'Bob', False),
			('>', 'Bob', 'Alice', True),

			('<>', 'Alice', 'Bob', True),
			('<>', 'Bob', 'Bob', False),
			('<>', 'Bob', 'Alice', True),
		]
		for op, lhs, rhs, expected_result in cases:
			expr = Comparision(op, Constant(lhs), Constant(rhs))
			self.assertEqual(expr.value_type(), bool)
			description = '%r %s %r' % (lhs, op, rhs)
			result = expr.evaluate([])
			self.assertIsNotNone(result, msg=description)
			self.assertEqual(result, expected_result, msg=description)
		# nullability, mixed types

	def test_should_return_null_if_operand_is_null(self):
		cases = [
			('<', None, 123, int),
			('=', 123, None, int),
			('<', None, 12.3, float),
			('<', None, 'hello', str),
			('=', None, False, bool),
			('<>', None, None, int),
			# Note: NULL <> NULL
			('=', None, None, int),
		]
		for op, lhs, rhs, operand_type in cases:
			expr = Comparision(op,
					Attribute(
						Column('A', operand_type, nullable=True, index=0)),
					Attribute(
						Column('B', operand_type, nullable=True, index=1)))
			self.assertTrue(expr.nullable())
			description = '%r %s %r %r' % (lhs, op, rhs, operand_type)
			result = expr.evaluate([lhs, rhs])
			self.assertIsNone(result, msg=description)

	def test_should_have_correct_nullability(self):
		cases = [
			(False, False, False),
			(False, True, True),
			(True, False, True),
			(True, True, True)
		]
		for lhs_null, rhs_null, result_null in cases:
			expr = Comparision('=',
					Attribute(
						Column('A', int, nullable=lhs_null, index=0)),
					Attribute(
						Column('B', int, nullable=rhs_null, index=1)))
			self.assertEqual(expr.nullable(), result_null)

	def test_should_return_error_if_operands_have_different_types(self):
		with self.assertRaisesRegex(TypeError, 'same type'):
			Comparision('=',
				Attribute(
					Column('A', bool, nullable=True, index=0)),
				Attribute(
					Column('B', int, nullable=True, index=1)))

# TODO:
# attributes - value type, nullability
# different types - throw error for now
# cast bool to int to float
# comparison - bool -> int -> float -> string
# nullability - short circuiting

if __name__ == '__main__':
	unittest.main()
