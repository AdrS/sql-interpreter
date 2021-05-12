#!/usr/bin/env python3

from relation import *
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

			('!=', 1, 2, True),
			('!=', 2, 2, False),
			('!=', 2, 1, True),

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

			('!=', 1.1, 2.2, True),
			('!=', 2.2, 2.2, False),
			('!=', 2.2, 1.1, True),

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

			('!=', False, True, True),
			('!=', True, True, False),
			('!=', True, False, True),

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

			('!=', 'Alice', 'Bob', True),
			('!=', 'Bob', 'Bob', False),
			('!=', 'Bob', 'Alice', True),
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
			('!=', None, None, int),
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

class TestSelection(unittest.TestCase):
	def test_should_return_error_for_non_boolean_expression(self):
		for incorrect_type in (int, float, str):
			with self.assertRaisesRegex(TypeError, 'Predicate'):
				Selection(MaterialRelation([Column('x', int)]),
				ValueExpression(None, incorrect_type))

	def test_should_have_same_columns_as_input(self):
		relation = Selection(MaterialRelation([
			Column('name', str, nullable=False),
			Column('age', int, nullable=True)
		], name='Users'),
		Constant(False))

		self.assertEqual(len(relation.columns), 2)
		self.assertEqual(relation.columns[0].name, 'name')
		self.assertEqual(relation.columns[0].type, str)
		self.assertEqual(relation.columns[0].nullable, False)
		self.assertEqual(relation.columns[0].index, 0)
		self.assertEqual(relation.columns[1].name, 'age')
		self.assertEqual(relation.columns[1].type, int)
		self.assertEqual(relation.columns[1].nullable, True)
		self.assertEqual(relation.columns[1].index, 1)

		self.assertIsNone(relation.name)
		relation.set_name('NoUsers')
		self.assertEqual(relation.name, 'NoUsers')

	def test_should_return_elements_matching_predicate(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int), Column('female', bool)
		])
		relation.insert(('Alice', 25, True))
		relation.insert(('Bob', 24, False))
		relation.insert(('Eve', 21, True))
		relation.insert(('Mallory', 35, True))

		selection = Selection(relation,
						Or(Comparison('<', Attribute(relation.columns[1]),
											Constant(24)),
							LogicalNot(Attribute(relation.columns[2]))))
		self.assertEqual(list(selection),
						[('Bob', 24, False), ('Eve', 21, True)])

	def test_should_not_return_elements_where_predicate_is_null(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int, nullable=True),
		])
		relation.insert(('Alice', 25))
		relation.insert(('Bob', 24))
		relation.insert(('Eve', 21))
		relation.insert(('Mallory', None))

		selection = Selection(relation, Comparison('<',
											Attribute(relation.columns[1]),
											Constant(24)))
		self.assertEqual(list(selection), [('Eve', 21)])

class TestGeneralizedProjection(unittest.TestCase):
	def test_should_have_schema(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int, nullable=True),
			Column('female', bool, nullable=False)
		])
		projection = GeneralizedProjection(relation, [
			Arithmetic('-', Constant(2021), Attribute(relation.columns[1])),
			LogicalNot(Attribute(relation.columns[2])),
		])
		self.assertEqual(len(projection.columns), 2)
		self.assertEqual(projection.columns[0].type, int)
		self.assertEqual(projection.columns[0].nullable, True)
		self.assertEqual(projection.columns[0].index, 0)
		self.assertEqual(projection.columns[1].type, bool)
		self.assertEqual(projection.columns[1].nullable, False)
		self.assertEqual(projection.columns[1].index, 1)

	def test_should_have_expected_column_names(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int)
		])
		projection = GeneralizedProjection(relation, [
			Attribute(relation.columns[0]),
			Cast(Attribute(relation.columns[1]), float),
			Arithmetic('-', Constant(2021), Attribute(relation.columns[1])),
		])
		self.assertEqual(len(projection.columns), 3)
		self.assertEqual(projection.columns[0].name, 'name')
		self.assertEqual(projection.columns[1].name, 'age')
		self.assertEqual(projection.columns[2].name, None)

	def test_should_generate_output(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int, nullable=True),
			Column('female', bool, nullable=False)
		])
		relation.insert(('Alice', 25, True))
		relation.insert(('Bob', 24, False))
		relation.insert(('Eve', 21, True))
		relation.insert(('Mallory', 35, True))

		projection = GeneralizedProjection(relation, [
			Arithmetic('-', Constant(2021), Attribute(relation.columns[1])),
			LogicalNot(Attribute(relation.columns[2]))
		])

		self.assertEqual(list(projection),
					[(1996, False), (1997, True), (2000, False), (1986, False)])

class TestNextValue(unittest.TestCase):
	def test(self):
		a = [1,2,3]
		it = a.__iter__()

		self.assertEqual(next_value(it), 1)
		self.assertEqual(next_value(it), 2)
		self.assertEqual(next_value(it), 3)
		self.assertIsNone(next_value(it))
		self.assertIsNone(next_value(it))

class TestRemoveDuplicates(unittest.TestCase):
	def test_empty_stream(self):
		self.assertEqual(list(remove_duplicates([].__iter__())), [])

	def test_removes_duplicates(self):
		cases = [
			([], []),
			([1, 2, 3], [1, 2, 3]),
			([1, 1, 2, 2, 3, 3], [1, 2, 3]),
		]
		for dupes, deduped in cases:
			self.assertEqual(list(remove_duplicates(dupes.__iter__())), deduped)

class TestStreamUnion(unittest.TestCase):
	def test(self):
		cases = [
			([], [1, 2, 3, 3], [1, 2, 3, 3]),
			([1, 3], [2, 4], [1, 2, 3, 4]),
			([1, 3], [3, 4], [1, 3, 3, 4]),
		]
		for a, b, u in cases:
			self.assertEqual(list(stream_union(a.__iter__(), b.__iter__())), u)
			self.assertEqual(list(stream_union(b.__iter__(), a.__iter__())), u)

class TestStreamIntersection(unittest.TestCase):
	def test(self):
		cases = [
			([], [1, 2, 3, 3], []),
			([1, 3], [2, 4], []),
			([1, 3], [3, 4], [3]),
			([1, 3, 3, 4], [3, 4], [3, 3, 3, 4]),
		]
		for a, b, i in cases:
			self.assertEqual(
				list(stream_intersection(a.__iter__(), b.__iter__())), i)
			self.assertEqual(
				list(stream_intersection(b.__iter__(), a.__iter__())), i)

class TestStreamDifference(unittest.TestCase):
	def test(self):
		cases = [
			([], [1, 2, 3, 3], []),
			([1, 2, 3, 3], [], [1, 2, 3, 3]),
			([1, 3], [2, 4], [1, 3]),
			([1, 1, 3, 3], [3, 4], [1]),
		]
		for a, b, d in cases:
			self.assertEqual(
				list(stream_difference(a.__iter__(), b.__iter__())), d)


class TestStreamIntersection(unittest.TestCase):
	def test(self):
		lhs = [1, 1, 1, 3, 4, 5, 5, 6].__iter__()
		rhs = [1, 4, 6, 7].__iter__()
		self.assertEqual(list(stream_intersection(lhs, rhs)),
				[1, 1, 1, 1, 4, 4, 6, 6])

class TestStreamDifference(unittest.TestCase):
	def test(self):
		lhs = [1, 1, 1, 3, 4, 5, 5, 6].__iter__()
		rhs = [1, 4, 6, 7].__iter__()
		self.assertEqual(list(stream_difference(lhs, rhs)), [3, 5, 5])

class TestCompareTuples(unittest.TestCase):
	def test(self):
		test_cases = [
			((2, 3), (2, 4), True, -1),
			((2, 3), (2, 3), True, 0),
			((2, 4), (2, 3), True, 1),
			((2, 3), (2, None), True, -1),
			((2, 3), (2, None), False, 1),
			((2, None), (2, 3), True, 1),
			((2, None), (2, 3), False, -1),
			((None, 2), (None, 2), True, 0),
			((None, 2), (None, 3), True, -1),
			((None, 3), (None, 2), True, 1),
		]
		for lhs, rhs, nulls_last, expected in test_cases:
			self.assertEqual(compare_tuples(lhs, rhs, nulls_last), expected,
				msg='%r < %r %r' % (lhs, rhs, nulls_last))

class TestSort(unittest.TestCase):
	def test_should_sort_ascending_by_default(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int),
		])
		relation.insert(('Mallory', 35))
		relation.insert(('Alice', 13))
		relation.insert(('Bob', 24))
		relation.insert(('Alice', 25))

		ordered = Sort(relation)
		self.assertEqual(list(ordered),
			[('Alice', 13), ('Alice', 25), ('Bob', 24), ('Mallory', 35)])

	def test_descending(self):
		relation = MaterialRelation([Column('name', str)])
		relation.insert(('Mallory',))
		relation.insert(('Alice',))
		relation.insert(('Bob',))

		ordered = Sort(relation, descending=True)
		self.assertEqual(list(ordered), [('Mallory',), ('Bob',), ('Alice',)])

	def test_should_sort_by_attributes(self):
		relation = MaterialRelation([
			Column('name', str), Column('age', int),
		])
		relation.insert(('Mallory', 35))
		relation.insert(('Alice', 13))
		relation.insert(('Bob', 24))
		relation.insert(('Alice', 25))

		ordered = Sort(relation,
						sort_key=[relation.columns[1], relation.columns[0]])
		self.assertEqual(list(ordered),
			[('Alice', 13), ('Bob', 24), ('Alice', 25), ('Mallory', 35)])

	def test_sort_orders_null_first(self):
		relation = MaterialRelation([
			Column('age', int, nullable=True),
		])
		relation.insert((35,))
		relation.insert((13,))
		relation.insert((None,))
		relation.insert((25,))

		ordered = Sort(relation, nulls_last=False)
		self.assertEqual(list(ordered), [(None,), (13,), (25,), (35,)])

	def test_sort_orders_null_last_by_default(self):
		relation = MaterialRelation([
			Column('age', int, nullable=True),
		])
		relation.insert((35,))
		relation.insert((13,))
		relation.insert((None,))
		relation.insert((25,))

		ordered = Sort(relation)
		self.assertEqual(list(ordered), [(13,), (25,), (35,), (None,)])

	def test_should_have_same_columns_as_input(self):
		relation = Sort(MaterialRelation([
			Column('name', str, nullable=False),
			Column('age', int, nullable=True)
		], name='Users'))

		self.assertEqual(len(relation.columns), 2)
		self.assertEqual(relation.columns[0].name, 'name')
		self.assertEqual(relation.columns[0].type, str)
		self.assertEqual(relation.columns[0].nullable, False)
		self.assertEqual(relation.columns[0].index, 0)
		self.assertEqual(relation.columns[1].name, 'age')
		self.assertEqual(relation.columns[1].type, int)
		self.assertEqual(relation.columns[1].nullable, True)
		self.assertEqual(relation.columns[1].index, 1)

		self.assertIsNone(relation.name)

class TestUnion(unittest.TestCase):
	def test_should_return_error_for_varying_tuple_length(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs = MaterialRelation([Column('a', str)])
		with self.assertRaisesRegex(ValueError, 'number of columns'):
			Union(lhs, rhs)

	def test_should_return_error_if_relations_have_different_column_types(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs = MaterialRelation([Column('a', str), Column('b', str)])
		with self.assertRaisesRegex(ValueError, 'column types'):
			Union(lhs, rhs)

	def test_should_return_duplicate_tuples_for_union_all(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))
		lhs.insert(('ca', 456))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		union = Union(lhs, rhs, distinct=False)
		self.assertEqual(list(union), [('au', 123), ('ca', 456), ('ca', 456),
			('ca', 456), ('ch', 789), ('fr', 123)])

	def test_should_omit_duplicate_tuples_for_union_distinct(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))
		lhs.insert(('ca', 456))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		union = Union(lhs, rhs, distinct=True)
		self.assertEqual(list(union),
			[('au', 123), ('ca', 456), ('ch', 789), ('fr', 123)])

	def test_should_merge_relations_with_different_column_names(self):
		lhs = MaterialRelation([Column('a', str)])
		lhs.insert(('au',))

		rhs = MaterialRelation([Column('b', str)])
		rhs.insert(('fr',))
		union = Union(lhs, rhs)
		self.assertEqual(list(union), [('au',), ('fr',)])

	def test_should_use_first_relations_column_names_for_output(self):
		lhs = MaterialRelation([Column('a', str), Column('x', int)])
		rhs = MaterialRelation([Column('b', str), Column('y', int)])
		union = Union(lhs, rhs)
		self.assertEqual(len(union.columns), 2)
		self.assertEqual(union.columns[0].name, 'a')
		self.assertEqual(union.columns[0].index, 0)
		self.assertEqual(union.columns[1].name, 'x')
		self.assertEqual(union.columns[1].index, 1)

	def test_should_be_nullable_when_any_input_relation_is_nullable(self):
		lhs = MaterialRelation([
			Column('a', str, nullable=False),
			Column('b', int, nullable=False),
		])
		rhs = MaterialRelation([
			Column('a', str, nullable=False),
			Column('b', int, nullable=True),
		])
		union = Union(lhs, rhs)
		self.assertFalse(union.columns[0].nullable)
		self.assertTrue(union.columns[1].nullable)

class TestIntersection(unittest.TestCase):
	def test_should_return_duplicate_tuples_for_intersection_all(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))
		lhs.insert(('ca', 456))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		intersection = Intersection(lhs, rhs, distinct=False)
		self.assertEqual(list(intersection), [('ca', 456), ('ca', 456),
			('ca', 456)])

	def test_should_omit_duplicate_tuples_for_intersection_distinct(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))
		lhs.insert(('ca', 456))
		lhs.insert(('ch', 789))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		intersection = Intersection(lhs, rhs, distinct=True)
		self.assertEqual(list(intersection), [('ca', 456), ('ch', 789)])
		self.assertTrue(intersection.columns[1].nullable)

class TestDifference(unittest.TestCase):
	def test_should_return_duplicate_tuples_for_difference_all(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		difference = Difference(lhs, rhs, distinct=False)
		self.assertEqual(list(difference), [('au', 123), ('au', 123)])

	def test_should_omit_duplicate_tuples_for_difference_distinct(self):
		lhs = MaterialRelation([Column('a', str), Column('b', int)])
		lhs.insert(('au', 123))
		lhs.insert(('au', 123))
		lhs.insert(('ca', 456))

		rhs = MaterialRelation([Column('a', str), Column('b', int)])
		rhs.insert(('fr', 123))
		rhs.insert(('ca', 456))
		rhs.insert(('ch', 789))

		difference = Difference(lhs, rhs, distinct=True)
		self.assertEqual(list(difference), [('au', 123)])

# TODO:
# COUNT(*) - number of input rows
# COUNT(expr) - number of rows expression is not null

class TestGroupBy(unittest.TestCase):
	def test_should_have_correct_schema(self):
		relation = MaterialRelation([Column('a', str, nullable=True),
				Column('b', bool, nullable=False),
				Column('c', int)])
		output = GroupBy(relation, relation.columns[:2], [CountFactory()])

		self.assertEqual(len(output.columns), 3)
		self.assertEqual(output.columns[0].name, 'a')
		self.assertEqual(output.columns[0].type, str)
		self.assertEqual(output.columns[0].nullable, True)
		self.assertEqual(output.columns[0].index, 0)
		self.assertEqual(output.columns[1].name, 'b')
		self.assertEqual(output.columns[1].type, bool)
		self.assertEqual(output.columns[1].nullable, False)
		self.assertEqual(output.columns[1].index, 1)
		self.assertEqual(output.columns[2].name, None)
		self.assertEqual(output.columns[2].type, int)
		self.assertEqual(output.columns[2].nullable, False)
		self.assertEqual(output.columns[2].index, 2)

	# TODO:
	# Function, type, nullable?
	# count, int, false
	# min, * , true
	# max, * , true
	# sum, <numeric>, false (default is 0)
	# avg - no tuples, no non-null values, non-numeric expression type

	# sum - null values, non-numeric expression type
	# sum - only valid for numeric types
	#	- what if expression evaluates to null for non-null input?
	#	- SUM(NULL)
	#	- default value of sum is 0 (all null input)
	# min, max - int, str, float, ...
	# count if

	# group by - nth column

# Expressions involving aggregates
# SELECT MAX(x) - MIN(x) FROM R GROUP BY y;

class TestCrossJoin(unittest.TestCase):
	def test(self):
		lhs = MaterialRelation([
			Column('id', int, nullable=False),
			Column('name', str, nullable=False)
		])
		lhs.insert((1, 'Alice'))
		lhs.insert((2, 'Bob'))
		lhs.insert((3, 'Eve'))

		rhs = MaterialRelation([
			Column('x', str, nullable=True),
			Column('y', bool, nullable=True),
			Column('z', float, nullable=False),
		])
		rhs.insert(('x', False, 3.14))
		rhs.insert(('X', True, 2.71))

		product = CrossJoin(lhs, rhs)
		self.assertEqual(len(product.columns), 5)
		self.assertEqual(product.columns[0].name, 'id')
		self.assertEqual(product.columns[0].type, int)
		self.assertFalse(product.columns[0].nullable)
		self.assertEqual(product.columns[0].index, 0)
		self.assertEqual(product.columns[1].name, 'name')
		self.assertEqual(product.columns[1].type, str)
		self.assertFalse(product.columns[1].nullable)
		self.assertEqual(product.columns[1].index, 1)
		self.assertEqual(product.columns[2].name, 'x')
		self.assertEqual(product.columns[2].type, str)
		self.assertTrue(product.columns[2].nullable)
		self.assertEqual(product.columns[2].index, 2)
		self.assertEqual(product.columns[3].name, 'y')
		self.assertEqual(product.columns[3].type, bool)
		self.assertTrue(product.columns[3].nullable)
		self.assertEqual(product.columns[3].index, 3)
		self.assertEqual(product.columns[4].name, 'z')
		self.assertEqual(product.columns[4].type, float)
		self.assertFalse(product.columns[4].nullable)

		self.assertEqual(list(product), [
			(1, 'Alice', 'x', False, 3.14),
			(1, 'Alice', 'X', True, 2.71),
			(2, 'Bob', 'x', False, 3.14),
			(2, 'Bob', 'X', True, 2.71),
			(3, 'Eve', 'x', False, 3.14),
			(3, 'Eve', 'X', True, 2.71),
		])

	def test_should_allow_multiple_columns_with_same_name(self):
		lhs = MaterialRelation([
			Column('a', int),
			Column('b', str)
		])
		lhs.insert((1, 'Alice'))
		lhs.insert((2, 'Bob'))
		lhs.insert((3, 'Eve'))

		rhs = MaterialRelation([
			Column('b', str, nullable=True),
			Column('c', bool, nullable=True),
		])
		rhs.insert(('x', False))
		rhs.insert(('X', True))

		product = CrossJoin(lhs, rhs)

		self.assertEqual(len(product.columns), 4)
		self.assertEqual(product.columns[0].name, 'a')
		self.assertEqual(product.columns[1].name, 'b')
		self.assertEqual(product.columns[2].name, 'b')
		self.assertEqual(product.columns[3].name, 'c')

		self.assertEqual(list(product), [
			(1, 'Alice', 'x', False),
			(1, 'Alice', 'X', True),
			(2, 'Bob', 'x', False),
			(2, 'Bob', 'X', True),
			(3, 'Eve', 'x', False),
			(3, 'Eve', 'X', True),
		])

# TODO:
# - expression in select predicate, generalized projection, or aggregation
#   references columns not in the input relation
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
