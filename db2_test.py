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

class ValueExpression(Expression):
	def __init__(self, value, expression_type, nullable=True):
		self.value = value
		self.type = expression_type
		self.is_nullable = nullable

	def value_type(self):
		return self.type

	def nullable(self):
		return self.is_nullable

	def evaluate(self, row):
		return self.value

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
			expr = Comparison(op, Constant(lhs), Constant(rhs))
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
			expr = Comparison(op,
					ValueExpression(lhs, operand_type, nullable=True),
					ValueExpression(rhs, operand_type, nullable=True))
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
			expr = Comparison('=',
					ValueExpression(0, int, nullable=lhs_null),
					ValueExpression(0, int, nullable=rhs_null))
			self.assertEqual(expr.nullable(), result_null)

	def test_should_return_error_if_operands_have_different_types(self):
		with self.assertRaisesRegex(TypeError, 'same type'):
			Comparison('=',
				ValueExpression(None, bool),
				ValueExpression(None, int))

class TestCastExpression(unittest.TestCase):
	def test_should_cast_bool_to_bool(self):
		for b in (False, True, None):
			expr = Cast(ValueExpression(b, bool, nullable=True), bool)
			self.assertEqual(expr.evaluate([]), b)

	def test_should_cast_integer_to_bool(self):
		cases = [
			(0, False),
			(1, True),
			(-123, True),
			(123, True),
			(None, None),
		]
		for i, b in cases:
			expr = Cast(ValueExpression(i, int, nullable=True), bool)
			self.assertEqual(expr.evaluate([]), b)

	def test_should_return_error_casting_float_to_bool(self):
		for f in (0.0, 1.0, -123.123, 3.14, None):
			with self.assertRaisesRegex(TypeError, 'FLOAT'):
				Cast(ValueExpression(f, float, nullable=True), bool)

	def test_should_cast_valid_string_to_bool(self):
		cases = [
			('false', False),
			('FALSE', False),
			('0', False),
			('true', True),
			('True', True),
			('1', True),
			(None, None)
		]
		for s, b in cases:
			expr = Cast(ValueExpression(s, str, nullable=True), bool)
			self.assertEqual(expr.evaluate([]), b)

	def test_should_return_error_casting_invalid_string_to_bool(self):
		for s in ('asf', '123', '1.0', 'unknown', 'null', ''):
			expr = Cast(ValueExpression(s, str, nullable=True), bool)
			with self.assertRaisesRegex(TypeError, 'invalid boolean'):
				expr.evaluate([])

	def test_should_cast_to_integer(self):
		cases = [
			(bool, False, 0),
			(bool, True, 1),
			(bool, None, None),
			(int, 123, 123),
			(int, None, None),
			(float, 123.0, 123),
			(float, 123.45, 123),
			(float, 0.45, 0),
			(float, -0.45, 0),
			(float, -123.45, -123),
			(float, None, None),
			(str, '-123', -123),
			(str, '123', 123),
			(str, '0', 0),
			(str, None, None),
		]
		for src_type, value, expected in cases:
			expr = Cast(ValueExpression(value, src_type, nullable=True), int)
			self.assertEqual(expr.evaluate([]), expected)

	def test_should_return_error_casting_invalid_string_to_integer(self):
		for s in ('asf', '3.14', '0x123', 'unknown', 'null', ''):
			expr = Cast(ValueExpression(s, str, nullable=True), int)
			with self.assertRaisesRegex(TypeError, 'invalid integer'):
				expr.evaluate([])

	def test_should_return_error_casting_bool_to_float(self):
		for b in (False, True, None):
			with self.assertRaisesRegex(TypeError, 'Cannot cast'):
				Cast(ValueExpression(b, bool, nullable=True), float)

	def test_should_cast_to_float(self):
		cases = [
			(int, 123, 123.0),
			(int, None, None),
			(float, 123.0, 123.0),
			(float, 123.45, 123.45),
			(float, None, None),
			(str, '-123', -123),
			(str, '123', 123),
			(str, '0', 0),
			(str, '-123.45', -123.45),
			(str, None, None),
		]
		for src_type, value, expected in cases:
			expr = Cast(ValueExpression(value, src_type, nullable=True), float)
			self.assertEqual(expr.evaluate([]), expected)

	def test_should_return_error_casting_invalid_string_to_float(self):
		for s in ('asf', '0x123', 'unknown', 'null', ''):
			expr = Cast(ValueExpression(s, str, nullable=True), float)
			with self.assertRaisesRegex(TypeError, 'invalid float'):
				expr.evaluate([])

	def test_should_cast_to_str(self):
		cases = [
			(bool, False, 'false'),
			(bool, True, 'true'),
			(bool, None, None),
			(int, 123, '123'),
			(int, -123, '-123'),
			(int, None, None),
			(float, 123.0, '123.0'),
			(float, 123.45, '123.45'),
			(float, None, None),
			(str, '', ''),
			(str, 'abc', 'abc'),
			(str, None, None),
		]
		for src_type, value, expected in cases:
			expr = Cast(ValueExpression(value, src_type, nullable=True), str)
			self.assertEqual(expr.evaluate([]), expected)

class TestAnd(unittest.TestCase):
	def test_should_evaluate_for_booleans(self):
		cases= [
			(None, None, None),
			(None, False, False),
			(None, True, None),
			(False, None, False),
			(False, False, False),
			(False, True, False),
			(True, None, None),
			(True, False, False),
			(True, True, True),
		]
		for lhs, rhs, expected_result in cases:
			expr = And(ValueExpression(lhs, bool),
					ValueExpression(rhs, bool))
			display = '%r AND %r' % (lhs, rhs)
			self.assertEqual(expr.evaluate([]), expected_result, msg=display)

	def test_should_return_type_error_for_non_booleans(self):
		for incorrect_type in (int, float, str):
			with self.assertRaisesRegex(TypeError, 'boolean'):
				And(ValueExpression(None, incorrect_type, nullable=True),
					ValueExpression(True, bool))
			with self.assertRaisesRegex(TypeError, 'boolean'):
				And(ValueExpression(True, bool),
					ValueExpression(None, incorrect_type, nullable=True))

class TestOr(unittest.TestCase):
	def test_should_evaluate_for_booleans(self):
		cases= [
			(None, None, None),
			(None, False, None),
			(None, True, True),
			(False, None, None),
			(False, False, False),
			(False, True, True),
			(True, None, True),
			(True, False, True),
			(True, True, True),
		]
		for lhs, rhs, expected_result in cases:
			expr = Or(ValueExpression(lhs, bool),
					ValueExpression(rhs, bool))
			display = '%r OR %r' % (lhs, rhs)
			self.assertEqual(expr.evaluate([]), expected_result, msg=display)

	def test_should_return_type_error_for_non_booleans(self):
		for incorrect_type in (int, float, str):
			with self.assertRaisesRegex(TypeError, 'boolean'):
				Or(ValueExpression(None, incorrect_type, nullable=True),
					ValueExpression(True, bool))
			with self.assertRaisesRegex(TypeError, 'boolean'):
				Or(ValueExpression(True, bool),
					ValueExpression(None, incorrect_type, nullable=True))

class TestArithmetic(unittest.TestCase):
	def test_should_return_error_for_non_numeric_types(self):
		for incorrect_type in (bool, str):
			with self.assertRaisesRegex(TypeError, 'numeric'):
				Arithmetic('+',
					ValueExpression(None, incorrect_type, nullable=True),
					ValueExpression(0, int))
			with self.assertRaisesRegex(TypeError, 'numeric'):
				Arithmetic('+',
					ValueExpression(0, int),
					ValueExpression(None, incorrect_type, nullable=True))

	def test_should_produce_numeric_type(self):
		cases = [
			('*', 7, 3, 7*3, int),
			('*', 7, 3.1, 7*3.1, float),
			('*', 7.1, 3, 7.1*3, float),
			('*', 7.4, 3.2, 7.4*3.2, float),
			('/', 7, 3, 2, int), # integer division
			('/', 7, 3.1, 7/3.1, float),
			('/', 7.1, 3, 7.1/3, float),
			('/', 7.4, 3.2, 7.4/3.2, float),
			('%', 7, 3, 7%3, int),
			('%', 7, 3.1, 7%3.1, float),
			('%', 7.1, 3, 7.1%3, float),
			('%', 7.4, 3.2, 7.4%3.2, float),
			('+', 7, 3, 7+3, int),
			('+', 7, 3.1, 7+3.1, float),
			('+', 7.1, 3, 7.1+3, float),
			('+', 7.4, 3.2, 7.4+3.2, float),
			('-', 7, 3, 7-3, int),
			('-', 7, 3.1, 7-3.1, float),
			('-', 7.1, 3, 7.1-3, float),
			('-', 7.4, 3.2, 7.4-3.2, float)
		]
		for op, lhs, rhs, expected_value, expected_type in cases:
			expr = Arithmetic(op, Constant(lhs), Constant(rhs))
			display = '%d %s %d' % (lhs, op, rhs)
			self.assertEqual(expr.value_type(), expected_type, msg=display)
			self.assertEqual(expr.evaluate([]), expected_value, msg=display)

	def test_should_do_integer_division(self):
		expr = Arithmetic('/', ValueExpression(7, int), ValueExpression(3, int))
		self.assertEqual(expr.value_type(), int)
		self.assertEqual(expr.evaluate([]), 2)

class TestUnaryMinus(unittest.TestCase):
	def test_should_return_error_for_non_numeric_type(self):
		for incorrect_type in (bool, str):
			with self.assertRaisesRegex(TypeError, 'must be numeric'):
				UnaryMinus(ValueExpression(None, incorrect_type, nullable=True))

	def test_should_return_same_numeric_type_as_operand(self):
		cases = [
			(int, 123, -123),
			(int, -123, 123),
			(float, 3.14, -3.14),
			(int, None, None),
			(float, None, None)
		]
		for operand_type, operand, expected_value in cases:
			expr = UnaryMinus(
					ValueExpression(operand, operand_type, nullable=True))
			self.assertEqual(expr.value_type(), operand_type)
			self.assertEqual(expr.evaluate([]), expected_value)

class TestLogicalNot(unittest.TestCase):
	def test_should_return_error_for_non_boolean_types(self):
		for incorrect_type in (int, float, str):
			with self.assertRaisesRegex(TypeError, 'must be boolean'):
				LogicalNot(ValueExpression(None, incorrect_type, nullable=True))

	def test_should_evaluate_to_expected_values(self):
		cases = [
			(False, True),
			(True, False),
			(None, None)
		]
		for operand, expected_value in cases:
			expr = LogicalNot(
					ValueExpression(operand, bool, nullable=True))
			self.assertEqual(expr.value_type(), bool)
			self.assertEqual(expr.evaluate([]), expected_value)

class TestIsNull(unittest.TestCase):
	def test_should_evaluate_to_expected_values(self):
		cases = [
			(bool, True, False),
			(bool, None, True),
			(int, 123, False),
			(int, None, True),
			(float, 3.14, False),
			(float, None, True),
			(str, '', False),
			(str, 'hello', False),
			(str, None, True),
		]
		for operand_type, operand, expected_value in cases:
			expr = IsNull(
					ValueExpression(operand, operand_type, nullable=True))
			self.assertEqual(expr.value_type(), bool)
			self.assertFalse(expr.nullable())
			self.assertEqual(expr.evaluate([]), expected_value)

class TestIsNotNull(unittest.TestCase):
	def test_should_evaluate_to_expected_values(self):
		cases = [
			(bool, True, True),
			(bool, None, False),
			(int, 123, True),
			(int, None, False),
			(float, 3.14, True),
			(float, None, False),
			(str, '', True),
			(str, 'hello', True),
			(str, None, False),
		]
		for operand_type, operand, expected_value in cases:
			expr = IsNotNull(
					ValueExpression(operand, operand_type, nullable=True))
			self.assertEqual(expr.value_type(), bool)
			self.assertFalse(expr.nullable())
			self.assertEqual(expr.evaluate([]), expected_value)

# nulls
# implicit conversions
# TODO: test type and nullability attributes

# TODO:
# attributes - value type, nullability
# different types - throw error for now
# implicit cast bool to int to float
# comparison - bool -> int -> float -> string
# nullability - short circuiting

if __name__ == '__main__':
	unittest.main()
