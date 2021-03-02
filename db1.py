#!/usr/bin/env python3

from collections import defaultdict
import operator

def normalize_name(name):
    return name.lower()

primative_types_by_name = {
    'integer': int,
    'string':str,
    'float':float,
    'boolean':bool
}

class ColumnSpec:
    def __init__(self, name, column_type):
        self.name = normalize_name(name)
        self.type = primative_types_by_name[normalize_name(column_type)]
        # TODO: null
        #self.not_null

class Schema:
    def __init__(self, columns, primary_key=[], descending=False):
        self.columns = columns
        self.column_index_by_name = {}
        for i, spec in enumerate(columns):
            if spec.name in self.column_index_by_name:
                raise ValueError("Multiple columns with name %r" % spec.name)
            self.column_index_by_name[spec.name] = i
        self.primary_key = self.column_indices(primary_key)
        self.descending = descending

    def column_indices(self, names):
        return [
            self.column_index_by_name[normalize_name(name)] for name in names]

class Bound:
    '''Describes and endpoint for a range request'''
    pass

class Unbounded(Bound):
    def in_bound(self, value):
        return True

class PointBound(Bound):
    def __init__(self, bound, op):
        self.bound = bound
        self.op = op

    def in_bound(self, value):
        for b, v in zip(self.bound, value):
            if self.op(b,v):
                return False
        return True

class ClosedLowerBound(PointBound):
    def __init__(self, bound):
        super().__init__(bound, operator.gt)

class OpenLowerBound(PointBound):
    def __init__(self, bound):
        super().__init__(bound, operator.ge)

class ClosedUpperBound(PointBound):
    def __init__(self, bound):
        super().__init__(bound, operator.lt)

class OpenUpperBound(PointBound):
    def __init__(self, bound):
        super().__init__(bound, operator.le)

def select_columns(row, indices):
    return [row[i] for i in indices]

class Table:
    def __init__(self, schema, rows=[]):
        self.schema = schema
        self.rows = []
        for row in rows:
            self.append(row)
        # TODO: replace with B+ tree

    def append(self, row):
        if len(row) != len(self.schema.columns):
            raise ValueError("Row has wrong number of columns")
        for value, spec in zip(row, self.schema.columns):
            if type(value) != spec.type:
                raise ValueError("Type of column %s must be %r" %
                        (spec.name, spec.type))
        self.rows.append(tuple(row))

    def sort_by_primary_key(self):
        if not self.schema.primary_key:
            return
        self.rows.sort(
                key=lambda row: select_columns(row, self.schema.primary_key),
                reverse=self.schema.descending)

    # TODO: return cursor to allow concurrent access
    def table_scan(self, column_indices):
        for row in self.rows:
            yield [row[i] for i in column_indices]

    def range_scan(self, low, high, key_indices, column_indices):
        for row in self.rows:
            key = select_columns(row, key_indices)
            if low.in_bound(key) and high.in_bound(key):
                yield select_columns(row, column_indices)

class Catalog:
    def __init__(self):
        self.tables = {}

    def create_table(self, name, schema):
        name = normalize_name(name)
        if name in self.tables:
            raise ValueError("Table %s already exists" % name)
        self.tables[name] = Table(schema)

    def __getitem__(self, name):
        name = normalize_name(name)
        if name not in self.tables:
            raise KeyError("Table %s does not exist" % name)
        return self.tables[name]

catalog = Catalog()

def create_table(name, columns):
    catalog.create_table(name, Schema(
        [ColumnSpec(col_name, col_type) for col_name, col_type in columns]))

def insert_into_table(name, values):
    table = catalog[name]
    for row in values:
        table.append(row)

class Select:
    def __init__(self, expressions, tables, where_predicate, group_by_keys=[]):
        tables_by_name = {}
        used_fields_by_table = defaultdict(set)
        for table_name in map(normalize_name(tables)):
            tables_by_name[table_name] = catalog[table_name]

    def print_results(self):
        pass

# Relation
# - fields = [(field name, field type, nullable) ...]
# - next tuple() -> tuple
# - project([field name ...]) -> relation
#
# Sorted Relation
# - relation 
# - sort order = [(field name, asc|dsc) ...]
#
# Table
# - relation
# read(field_names) -> relation
#
# filter(relation, predicate) -> relation
# select(relation, expressions) -> relation
# join(relation, relation) -> relation
# aggregate(relation, group_key, aggregations) -> relation
# sort(relation) ->

class Expression: pass

class Constant(Expression):
    def __init__(self, value):
        self.value = value
    def eval(self, row):
        return self.value

class Field(Expression):
    def __init__(self, index):
        self.index = index

    def eval(self, row):
        return row[self.index]

class UnaryOp(Expression):
    def __init__(self, value, op):
        assert(isinstance(value, Expression))
        self.value = value
        self.op = op

    def eval(self, row):
        return self.op(self.value.eval(row))

class BinaryOp(Expression):
    def __init__(self, lhs, rhs, op):
        assert(isinstance(lhs, Expression))
        assert(isinstance(rhs, Expression))
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def eval(self, row):
        return self.op(self.lhs.eval(row), self.rhs.eval(row))

def filter_rows(rows, predicate):
    for row in rows:
        if predicate.eval(row):
            yield row

def select_expressions(rows, expressions):
    for row in rows:
        yield [e.eval(row) for e in expressions]

class Aggregation: pass

class Count(Aggregation):
    def __init__(self):
        self.count = 0
    def update(self, value):
        self.count += 1
    def output(self):
        return self.count

class CountIf(Aggregation):
    def __init__(self):
        self.count = 0
    def update(self, value):
        if value:
            self.count += 1
    def output(self):
        return self.count

class Sum(Aggregation):
    def __init__(self):
        self.sum = 0
    def update(self, value):
        self.sum += value
    def output(self):
        return self.sum

class Avg(Aggregation):
    def __init__(self):
        self.count = 0
        self.sum = 0
    def update(self, value):
        self.sum += value
        self.count += 1
    def output(self):
        return self.sum/self.count

class Max(Aggregation):
    def __init__(self):
        self.max = None
    def update(self, value):
        if value != None and (self.max == None or value > self.max):
            self.max = value
    def output(self):
        return self.max

class Min(Aggregation):
    def __init__(self):
        self.min = None
    def update(self, value):
        if value != None and (self.min == None or value < self.min):
            self.min = value
    def output(self):
        return self.min

class AggregateExpression:
    def __init__(self, aggregation, expression):
        self.aggregation = aggregation
        self.expression = expression
    def update(self, row):
        self.aggregation.update(self.expression.eval(row))
    def output(self):
        return self.aggregation.output()

class AggregationFactory:
    def __init__(self, aggregation, expression):
        self.aggregation = aggregation
        self.expression = expression
    def make(self):
        return AggregateExpression(self.aggregation(), self.expression)

def hash_aggregate(rows, key_indices, aggregators):
    groups = defaultdict(lambda:[a.make() for a in aggregators])

    for row in rows:
        key = tuple(select_columns(row, key_indices))
        for aggregation in groups[key]:
            aggregation.update(row)

    for key, aggregations in groups.items():
        row = [v for v in key]
        for aggregation in aggregations:
            row.append(aggregation.output())
        yield row

def cross_join(lhs_rows, rhs_rows):
    for lhs_row in lhs_rows:
        for rhs_row in rhs_rows:
            row = []
            row.extend(lhs_row)
            row.extend(rhs_row)
            yield row

#def inner_hash_join(lhs_rows, rhs_rows, lhs_key_indices, rhs_key_indices):
# aggregation
#  - hash, sorting
# joins
#  - cross, sorting, hash
#  - left, right, inner, outer
# sorting

# CREATE TABLE <name> (
#   column1 type1,
#   ...
#   columnn typen
# );

# INSERT INTO <table name> VALUES (
#   (<expr1>, <expr2>, .., <exprn>),
#   ...
# );

# SELECT expr1, ..., exprn AS .
# FROM table1, ..., tablem
# WHERE predicate
# GROUP BY field1, ... fieldl
# TODO: having

create_table('Users', [
    ('UserId', 'INTEGER'),
    ('Name', 'STRING'),
    ('Email', 'STRING'),
    ('Lat', 'FLOAT'),
    ('Long', 'FLOAT'),
    ('Female', 'BOOLEAN'),
    ])

insert_into_table('Users', [
    (1, 'Adrian', 'adrs@umich.edu', 42.2, -83.8, False),
    (2, 'Watson', 'w@zoo.com', 42.2, -83.8, False),
    (3, 'Alice', 'alice@gmail.com', 50.5, 14.2, True),
    (4, 'Bob', 'bob@gmail.com', 59.6, 79.3, False),
    (5, 'Eve', 'eve@mail.ru', 55.45, 37.36, True),
    (6, 'Mallory', 'mal@mail.ru', 35.4, 139.45, True)
])

if __name__ == '__main__':
    users = Table(Schema([
        ColumnSpec('UserId', 'INTEGER'),
        ColumnSpec('Name', 'STRING'),
        ColumnSpec('Email', 'STRING'),
        ColumnSpec('Lat', 'FLOAT'),
        ColumnSpec('Long', 'FLOAT'),
        ColumnSpec('Female', 'BOOLEAN'),
        ],
        ['UserId']),
        rows = [
            (1, 'Adrian', 'adrs@umich.edu', 42.2, -83.8, False),
            (2, 'Watson', 'w@zoo.com', 42.2, -83.8, False),
            (3, 'Alice', 'alice@gmail.com', 50.5, 14.2, True),
            (4, 'Bob', 'bob@gmail.com', 59.6, 79.3, False),
            (5, 'Eve', 'eve@mail.ru', 55.45, 37.36, True),
            (6, 'Mallory', 'mal@mail.ru', 35.4, 139.45, True)
        ])

    f1 = BinaryOp(Field(0), Constant(90), operator.truediv)
    f2 = BinaryOp(Field(1), Constant(180), operator.truediv)
    f3 = BinaryOp(UnaryOp(f1, abs), UnaryOp(f2, abs), operator.gt)
    for row in select_expressions(filter_rows(
        users.table_scan(users.schema.column_indices(['Lat', 'Long', 'Name'])),
        f3), [Field(2), f1, f2]):
        print(row)

    for row in users.range_scan(ClosedLowerBound([2]), Unbounded(),
            users.schema.column_indices(['UserId']),
            users.schema.column_indices(['Name', 'Email'])):
        print(row)
    for row in hash_aggregate(
        users.table_scan(users.schema.column_indices(['Lat', 'Long', 'Female'])),
        [2], [
            AggregationFactory(Max, UnaryOp(Field(0), abs)), # Max(abs(Lat))
            AggregationFactory(Max, UnaryOp(Field(1), abs)), # Max(abs(Long))
        ]):
        print(row)

    for row in filter_rows(
        cross_join(
            tuple(users.table_scan(users.schema.column_indices(['Name',
                'Lat']))),
            tuple(users.table_scan(users.schema.column_indices(['Name', 'Lat'])))),
        BinaryOp(Field(1), Field(3), operator.lt)):
        print(row)
    # for row in cross_join(
    #         tuple(
    #             users.table_scan(users.schema.column_indices(['Name', 'Lat']))),
    #         tuple(
    #             users.table_scan(users.schema.column_indices(['Name', 'Lat'])))):
    #     print(row)
