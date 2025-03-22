import os

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER     = os.getenv("MYSQL_USER", "your_mysql_username")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_mysql_password")
MYSQL_DB       = os.getenv("MYSQL_DB", "asrank_dashboard")
