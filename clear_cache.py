import os
import mysql.connector
from config import config

cnx = mysql.connector.connect(**config["mysql"])
cursor = cnx.cursor()
cursor.execute("DROP DATABASE IF EXISTS js_analyzer;")
cnx.commit()
cursor.close()
cnx.close()

for root, dirs, files in os.walk("cache/"):
    for f in files:
        os.remove(os.path.join("cache/",f))
