import logging
import sqlite3
from config import DB_NAME, MAX_USERS, MAX_STT_MESSAGES


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)


def execute_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    logging.info(f"DATABASE: Execute query: {sql_query}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()


def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    logging.info(f"DATABASE: Execute query: {sql_query}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows


def create_table():
    sql_query = '''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                stt_blocks INTEGER)
                '''
    execute_query(sql_query)


def insert_row(values):
    sql_query = f"INSERT INTO messages (user_id, message, stt_blocks) VALUES (?, ?, ?)"
    execute_query(sql_query, values)


def is_limit_users(db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    result = cursor.execute(f'SELECT DISTINCT user_id FROM messages;')
    count = 0
    for i in result:
        count += 1
    connection.close()
    return count >= MAX_USERS


def is_limit_messages(user_id, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    result = cursor.execute(f'SELECT DISTINCT * FROM messages WHERE user_id = ?;', [user_id])
    count = 0
    for i in result:
        count += 1
    connection.close()
    return count >= MAX_STT_MESSAGES
