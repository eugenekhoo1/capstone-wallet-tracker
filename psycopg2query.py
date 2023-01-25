import psycopg2
import psycopg2.extras as extras
import pandas as pd

# Define settings

def query(sql_script):
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(
            host = # host,
            dbname = # dbname,
            user = # user,
            password = # password,
            port = # port
        )

        cur = conn.cursor()

        cur.execute(sql_script)
        data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

    except Exception as error:
        print(error)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    df = pd.DataFrame(data, columns=col_names)
    return df

def transactions(wallet, table): # used for pnl EDA
    conn = None
    cur = None

    try:
        # open database connection
        conn = psycopg2.connect(
            host = # host,
            dbname = # dbname,
            user = # user,
            password = # password,
            port = # port
        )

        # cursor to run sql query
        cur = conn.cursor()

        sql_script = f"""
        SELECT *, usd_value_at_txn / token_bought_amount as token_bought_price, usd_value_at_txn / token_sold_amount as token_sold_price
        FROM {table}
        WHERE tx_from = '{wallet}'
        """
        cur.execute(sql_script)
        data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
    except Exception as error:
        print(error)
    finally:
        if cur is not None:
            # close cursor
            cur.close()
        if conn is not None:
            # close database connection
            conn.close()
    df = pd.DataFrame(data, columns=col_names)
    return df

def insert_df_sql(df, table):
        # open database connection
    conn = psycopg2.connect(
            host = # host,
            dbname = # dbname,
            user = # user,
            password = # password,
            port = # port
            )

    # cursor to run sql query
    cur = conn.cursor()

    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    print(query)
    try:
        extras.execute_values(cur, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cur.close()
        return 1
    print("the dataframe is inserted")
    cur.close()
    conn.close()

