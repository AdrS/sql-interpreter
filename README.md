# SQL Interpreter

A SQL repl and query engine written in Python.

## Basic Usage

```
$ ./repl.py
$ create table pets (name string, species string, age integer);
Success!
$ insert into pets values ('Spot', 'dog', 3), ('Mittens', 'cat', 1), ('Fido',
'dog', 2);
Success!
$ select name from pets where species = 'dog';
('Spot',)
('Fido',)
$ select species, count(1) as population from pets group by species;
('cat', 1)
('dog', 2)
$
```

## Features

Supported features include:
- Schema definitions with create table
- Data manipulation with insert into
- Queries with selection, projection, aggregations, cross-joins, union, insertion, set difference, column and table aliases, casting, arithmetic and logic with nulls, and selection from nested queries.
- Command history and tab-completion of keywords, table, and column names.

For examples of all supported features, look at the unit tests in repl\_test.py.
