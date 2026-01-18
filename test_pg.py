import psycopg2

params = {
    "dbname": "helpdesk",
    "user": "helpdesk_user",
    "password": "helpdesk_password",  # 如果你改过密码，这里也改
    "host": "localhost",
    "port": "5432",
}

print("Trying to connect with params:", params)

conn = psycopg2.connect(**params)
print("Connected OK!")

conn.close()
print("Connection closed.")
