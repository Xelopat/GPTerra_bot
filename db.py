import mysql.connector
from mysql.connector import OperationalError, InterfaceError

sql_host = "localhost"
sql_db = "chat_gpt"
sql_user = "root"

sql_password = "root"  # local


# sql_password = "discount777"  # server


def connect():
    conn_f = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password, database=sql_db)
    return conn_f


def get_cursor():
    global conn
    try:
        return conn.cursor(buffered=True)
    except OperationalError:
        conn = connect()
    return conn.cursor(buffered=True)


def db_init():
    global conn
    conn1 = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password)
    cursor = conn1.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {sql_db}")
    conn1.commit()
    conn1.close()
    conn = connect()
    cursor = get_cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users("
                   "user_id BIGINT PRIMARY KEY,"
                   "model TEXT,"
                   "balance FLOAT DEFAULT 10,"
                   "refers INT DEFAULT 0,"
                   "date DATE DEFAULT (CURRENT_DATE)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS keys("
                   "openai_key TEXT,"
                   "balance INT,"
                   "login TEXT,"
                   "is_active BOOL DEFAULT 0"
                   ")")
    conn.commit()
    if not get_key():
        cursor.execute(f"INSERT INTO options(openai_key) VALUES('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')")
        conn.commit()
    cursor.close()


def change_key(error):
    global conn
    cursor = get_cursor()
    if error == "limit":
        cursor.execute(f"DELETE FROM keys WHERE is_active=1")
    else:
        cursor.execute(f"UPDATE keys SET balance=0, is_active=0 WHERE is_active=1")
    cursor.execute("UPDATE keys SET is_active=1 WHERE balance > 0 LIMIT 1")

def user_exists(user_id):
    global conn
    cursor = get_cursor()
    cursor.execute(f"SELECT 1 FROM users WHERE user_id={user_id}")
    is_exists = cursor.fetchone()
    cursor.close()
    cursor = get_cursor()
    if is_exists:
        return True
    cursor.execute(f"INSERT INTO users(user_id, model) VALUES({user_id}, 'gpt-3.5-turbo')")
    conn.commit()
    cursor.close()
    return False


def get_model(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT model FROM users WHERE user_id=%s", (user_id,))
        model = cursor.fetchone()[0]
        return model
    except Exception as e:
        print(e)
        return "text-davinci-003"


def get_statistic_day():
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT date, COUNT(1) FROM users "
                       f"WHERE DATE(date)<>'1977-01-01' AND TIMESTAMPDIFF(DAY, NOW(), DATE(date)) < 10 "
                       f"GROUP BY date "
                       f"ORDER BY date ASC")
        statistic = cursor.fetchall()
        return statistic
    except Exception as e:
        print(e)
        return []


def get_statistic_all():
    global conn
    try:
        cursor = get_cursor()
        cursor.execute("SELECT date, (SELECT COUNT(*) FROM users AS d2 "
                       "WHERE d2.date <= d1.date AND DATE(d2.date)<>'1977-01-01' AND "
                       "TIMESTAMPDIFF(DAY, NOW(), DATE(d2.date)) < 10)"
                       "FROM users AS d1 WHERE DATE(d1.date)<>'1977-01-01' AND "
                       "TIMESTAMPDIFF(DAY, NOW(), DATE(d1.date)) < 10 ORDER BY date")
        statistic = cursor.fetchall()
        return statistic
    except Exception as e:
        print(e)
        return []


def get_all_users(block=False):
    global conn
    try:
        cursor = get_cursor()
        if not block:
            extra = "WHERE DATE(date)<>'1977-01-01'"
        else:
            extra = ""
        cursor.execute(f"SELECT user_id FROM users {extra}")
        users = cursor.fetchall()
        return users
    except:
        return []


def get_balance(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT balance FROM users WHERE user_id={user_id}")
        balance = cursor.fetchone()
        return balance[0]
    except:
        return 0


def get_refers(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT refers FROM users WHERE user_id={user_id}")
        balance = cursor.fetchone()
        return balance[0]
    except:
        return 0


def get_key():
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT openai_key FROM options WHERE is_active=1")
        balance = cursor.fetchone()
        return balance[0]
    except:
        return 0


def new_key(openai_key, balance):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"INSERT INTO keys(openai_key, balance) VALUES(%s, %s)", (openai_key, balance))
        conn.commit()
        return 1
    except:
        return 0


def update_balance(user_id, balance):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE users SET balance=balance+{balance} WHERE user_id={user_id}")
        conn.commit()
        return 1
    except:
        return 0


def update_refers(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE users SET refers=refers+1 WHERE user_id={user_id}")
        conn.commit()
        return 1
    except:
        return 0


def update_model(user_id, model):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE users SET model=%s WHERE user_id=%s", (model, user_id))
        conn.commit()
        return 1
    except:
        return 0


def update_user(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE users SET date=NOW() WHERE user_id={user_id}")
        conn.commit()
        return 1
    except:
        return 0


def del_user(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE users SET date='1977-01-01' WHERE user_id={user_id}")
        conn.commit()
        return 1
    except:
        return 0


def update_key(key):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE options SET openai_key={key}")
        conn.commit()
        return 1
    except:
        return 0


def sql(request):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(request)
        try:
            if "select" in request.lower():
                response = cursor.fetchall()
            else:
                response = [["COMPLETE"]]
        except InterfaceError as e:
            response = [[e]]
        if not response:
            response = [["None"]]
        conn.commit()
        return response
    except Exception as e:
        return [[e]]


db_init()
conn = connect()
