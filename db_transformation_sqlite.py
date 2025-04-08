"""
Fetches database structure: Extracts tables, columns, and indexes, ensuring all SQL data types are supported.

Compares old and new databases: Identifies new, deleted, and modified tables and indexes.

Processes changes: Executes the necessary SQL statements to apply changes to the new database, such as adding/removing fields, creating or dropping tables, and updating indexes.
"""

import sqlite3
import json
import re

def db_structure(db_filepath):
    db = sqlite3.connect(db_filepath)
    db.text_factory = str
    cur = db.cursor()

    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name != 'sqlite_sequence';").fetchall()
    table_names = sorted(list(zip(*tables))[0])

    print("--Tables for database %s \n" % db_filepath)
    print("\n".join(table_names))
    print("\n")

    results = {}
    table_data = {}

    # Define all possible SQL data types
    sql_data_types = [
        "NOT NULL", "DATE", "SMALLINT", "PRIMARY KEY", "FOREIGN KEY", "AUTOINCREMENT",
        "NULL", "INTEGER", "CHAR", "VARCHAR", "REFERENCES", "DEFAULT", "CURRENT_TIMESTAMP",
        "not null", "smallint", "foreign key", "autoincrement", "references",
        "integer", "primary key", "char", "varchar", "current_timestamp", "boolean",
        "decimal", "float", "double", "numeric", "text"
    ]

    for table_name in table_names:
        columns_data = {}
        columns_schema = {}

        print("-- EXTRACTING TABLE %s" % table_name)

        # Get table columns via pragma_table_info
        result_pragma_table_info = cur.execute("select * from pragma_table_info('%s');" % table_name)

        for column_id, column_name, column_type, column_not_null, column_default, column_pk in result_pragma_table_info:

            id = column_id
            name = column_name
            type = column_type
            null = ""
            default = ""
            pk = ""

            if column_not_null:
                null = " NOT NULL"

            if column_default:
                default = "%s" % column_default

            if column_pk:
                pk = " *%s" % column_pk

            col_name = name
            col_schema = "%s %s %s %s" % (type, null, default, pk)

            # Normalize SQL data types to uppercase
            for tag in sql_data_types:
                col_schema = col_schema.replace(tag, tag.upper())

            print(col_name + "--> " + col_schema)

            columns_schema[col_name] = col_schema

        columns_data["columns"] = columns_schema

        # Get the original CREATE TABLE statement
        original = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' and name='%s';" % table_name).fetchall()

        for sql_stmt in original:
            columns_data["sql_stmt"] = " ".join(sql_stmt).replace("[", "").replace("]", "")

        # Get table foreign keys
        sql_pragma_foreign_list = """SELECT 
            m.name,
            p."table",
            p."from",
            p."to"
            FROM
            sqlite_master m
            JOIN pragma_foreign_key_list(m.name) p ON m.name != p."table"
            WHERE m.type = 'table' and m.name="%s"
            ORDER BY m.name;
        """ % table_name

        res = cur.execute(sql_pragma_foreign_list)

        foreign_keys = []

        print("- FOREIGN KEYS")

        for table, reference_table, table_from, table_refer_to in res:
            print(table + "->" + reference_table + " " + table_from + " " + table_refer_to)
            foreign_keys.append(reference_table + " " + table_from + " " + table_refer_to)

        columns_data["foreign_keys"] = foreign_keys

        print("--" * 30)

        table_data[table_name] = columns_data

    indexes = cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index' and name not like 'sqlite_autoindex%';").fetchall()

    index_data = {}
    for key, val in indexes:
        value = " ".join(val.split()).replace("[", "").replace("]", "")
        value = re.sub("\s*(\W)\s*", r"\1", value)  # Remove whitespace between special characters and words/letters

        index_data[key] = value

    results["TABLES"] = table_data
    results["INDEXES"] = index_data

    db.close()

    return results

def compare_results(old_contents, new_contents):
    old_contents_keys = set(old_contents.keys())
    new_contents_keys = set(new_contents.keys())
    intersect_keys = old_contents_keys.intersection(new_contents_keys)

    new = list(new_contents_keys - old_contents_keys)
    deleted = list(old_contents_keys - new_contents_keys)

    modified = {data: {"old_print": old_contents[data], "new_print": new_contents[data]} for data in intersect_keys if old_contents[data] != new_contents[data]}

    same = list(data for data in intersect_keys if old_contents[data] == new_contents[data])

    return new, deleted, modified, same

def execute_statement(sql_statement, db_to_transform):
    db = sqlite3.connect(db_to_transform)
    db.text_factory = str
    cur = db.cursor()
    cur.execute(sql_statement)
    db.close()

def process_new_table(_results, new_table_results, db_to_transform):
    if _results:
        print("- Process new tables")
        for new_table in _results:
            print("add new table `%s`" % new_table)
            sql_stmt = new_table_results[new_table]["sql_stmt"]
            print("sql statement %s" % sql_stmt)
            execute_statement(sql_stmt, db_to_transform)

def process_deleted_table(_results, db_to_transform):
    if _results:
        print("- Process deleted tables")
        for delete_table in _results:
            sql_stmt = "DROP TABLE %s;" % delete_table
            print("Deleting table %s " % delete_table)
            print("Sql Statement %s " % sql_stmt)
            execute_statement(sql_stmt, db_to_transform)

def process_modified_table(_results, new_table_results, db_to_transform):
    new_print = None
    old_print = None

    if _results:
        print("- Process modified tables")
        print(json.dumps(_results, indent=4))

        for table, val in _results.items():
            old_print = _results[table]["old_print"]["columns"]
            new_print = _results[table]["new_print"]["columns"]

            new_fields, deleted_fields, modified_fields, same_fields = compare_results(old_print, new_print)

            print("-- new field names for table `%s`" % table)
            print(json.dumps(new_fields, indent=2))

            print("-- deleted field names for table `%s`" % table)
            print(json.dumps(deleted_fields, indent=2))

            print("-- modified field names for table `%s`" % table)
            print(json.dumps(modified_fields, indent=2))

            # Process new fields
            if new_fields:
                for field_name in new_fields:
                    print("%s : %s" % (field_name, new_print[field_name]))
                    sql_stmt = _results[table]["new_print"]["sql_stmt"]
                    split_stmt = sql_stmt.split("\n")

                    fieldname_schema = None
                    for index, j in enumerate(split_stmt):
                        if field_name in j:
                            fieldname_schema = split_stmt[index]

                    clean_fieldname = fieldname_schema.strip()[:-1]

                    if "CURRENT_TIMESTAMP" in clean_fieldname:
                        new_print_clean = list(set(new_print.keys()) - set(new_fields))
                        drop_table = "DROP TABLE IF EXISTS %s_old;" % table
                        execute_statement(drop_table, db_to_transform)
                        rename_table = "ALTER TABLE %s RENAME TO %s_old;" % (table, table)
                        execute_statement(rename_table, db_to_transform)

                        sql_stmt = new_table_results[table]["sql_stmt"]
                        execute_statement(sql_stmt, db_to_transform)

                        new_fieldnames = ", ".join(new_print_clean)
                        insert_statement = "INSERT INTO %s (%s) SELECT %s FROM %s_old;" % (table, new_fieldnames, new_fieldnames, table)
                        print(insert_statement)
                        execute_statement(insert_statement, db_to_transform)

                        drop_table = "DROP TABLE IF EXISTS %s_old;" % table
                        execute_statement(drop_table, db_to_transform)

                        break
                    else:
                        add_new_field_statement = "ALTER TABLE %s ADD %s;" % (table, clean_fieldname)
                        print("Add new field name %s" % field_name)
                        print(add_new_field_statement)
                        execute_statement(add_new_field_statement, db_to_transform)

            # Process deleted fields
            if deleted_fields or modified_fields:
                drop_table = "DROP TABLE IF EXISTS %s_old;" % table
                execute_statement(drop_table, db_to_transform)
                rename_table = "ALTER TABLE %s RENAME TO %s_old;" % (table, table)
                execute_statement(rename_table, db_to_transform)

                sql_stmt = new_table_results[table]["sql_stmt"]
                execute_statement(sql_stmt, db_to_transform)

                new_fieldnames = ", ".join(new_print.keys())
                insert_statement = "INSERT INTO %s (%s) SELECT %s FROM %s_old;" % (table, new_fieldnames, new_fieldnames, table)
                execute_statement(insert_statement, db_to_transform)

                drop_table = "DROP TABLE IF EXISTS %s_old;" % table
                execute_statement(drop_table, db_to_transform)

def process_check_table_schemas(_results, new_table_results, db_to_transform):
    result_contents = "UPDATED"
    if _results:
        for table, val in _results.items():
            old_foreign_keys = _results[table]["old_print"]["foreign_keys"]
            new_foreign_keys = _results[table]["new_print"]["foreign_keys"]

            if set(old_foreign_keys) != set(new_foreign_keys):
                print("need to rerun the whole process, tables schema not the same!")
                result_contents = "NOT UPDATED"

    return result_contents

def process_new_index(_results, new_index_results, db_to_transform):
    if _results:
        print("- Process new indexes")
        for result in _results:
            sql_stmt = new_index_results[result]
            print("SQL STATEMENT %s" % sql_stmt)
            execute_statement(sql_stmt, db_to_transform)

def process_deleted_index(_results, db_to_transform):
    if _results:
        print("- Process deleted indexes")
        for result in _results:
            sql_stmt = "DROP INDEX %s;" % result
            execute_statement(sql_stmt, db_to_transform)

def main(db_filename_old, db_filename_new):
    result_first = db_structure(db_filename_old)
    result_second = db_structure(db_filename_new)

    print("\n---- Transform result for %s" % db_filename_old)
    print(json.dumps(result_first, indent=4))

    print("---- Transform result %s" % db_filename_new)
    print(json.dumps(result_second, indent=4))

    # Compare tables
    new_tables, deleted_tables, modified_tables, same_tables = compare_results(result_first["TABLES"], result_second["TABLES"])
    process_new_table(new_tables, result_second["TABLES"], db_filename_new)
    process_deleted_table(deleted_tables, db_filename_new)
    process_modified_table(modified_tables, result_second["TABLES"], db_filename_new)

    # Compare indexes
    new_indexes, deleted_indexes, modified_indexes, same_indexes = compare_results(result_first["INDEXES"], result_second["INDEXES"])
    process_new_index(new_indexes, result_second["INDEXES"], db_filename_new)
    process_deleted_index(deleted_indexes, db_filename_new)

    # Check table schema consistency
    result_check = process_check_table_schemas(modified_tables, result_second["TABLES"], db_filename_new)
    if result_check == "NOT UPDATED":
        print("-- TABLE SCHEMAS DO NOT MATCH. Retry migration.")
