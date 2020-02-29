"""Script to set up proxy as a cache.

Author:
    Jacinta Hu

About:
    This script intercepts requests and responses to act as a local cache
    alters the index.html file of webpages to easily enable and disable scripts.

"""

import os
import hashlib
import binascii
import pickle
import mysql.connector
from mitmproxy import http
from bs4 import BeautifulSoup
from config import config


class LocalCache:
    """The local client-side cache."""

    def __init__(self):
        self.path = os.getcwd()
        self.cnx = mysql.connector.connect(**config["mysql"])
        cursor = self.cnx.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS js_analyzer;")
        cursor.execute("USE js_analyzer;")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `resource_location` ("
            "   `hashed_url` CHAR(64) NOT NULL PRIMARY KEY,"
            "   `full_url` VARCHAR(2000) NOT NULL,"
            "   `file_name` CHAR(32) NOT NULL,"
            "   `datetime` DATETIME NOT NULL"
            ")"
        )
        self.cnx.commit()
        cursor.close()

    def __del__(self):
        self.cnx.close()

    def random_filename(self):
        """Generate a new unique random filename for the cache."""
        file_name = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
        while os.path.exists(self.path + "/cache/" + file_name + ".c"):
            file_name = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
        return file_name

    def request(self, flow: http.HTTPFlow):
        """Handle HTTP Request."""
        js_tool = False
        full_url = flow.request.pretty_url.split("?")[0]
        if "?JSTool=" in flow.request.pretty_url:
            full_url += "?JSTool"
            js_tool = True
        hashed_url = hashlib.sha256(full_url.encode()).hexdigest()
        cursor = self.cnx.cursor()
        cursor.execute(
            "SELECT `file_name` FROM resource_location "
            "WHERE `hashed_url` LIKE '%s'" %
            (hashed_url)
        )
        result = cursor.fetchone()
        if result:
            # found in db
            file_name = str(result[0])
            file_path = self.path + "/cache/" + file_name
            if js_tool:
                # headers
                with open(file_path + '.h', 'rb') as temp_file:
                    temp_headers = pickle.load(temp_file)

                headers_dict = {}
                for attr in list(temp_headers):
                    headers_dict[attr] = temp_headers[attr]

                # make simplification
                with open(file_path + '.c', 'rb') as temp_file:
                    temp_content = pickle.load(temp_file)

                html = str(BeautifulSoup(temp_content, 'html.parser'))
                active = flow.request.pretty_url.split(
                    "?JSTool=")[-1].split("_")
                active = active[1:]
                for num in active:
                    index = html.find("<!--script" + str(num) + "\n")
                    html = html.replace(
                        "<!--script" + str(num) + "\n", "<script")
                    html = html[0:index] + \
                        html[index:].replace("-->\n", "</script>", 1)

                # return response
                flow.response = http.HTTPResponse.make(
                    200,  # (optional) status code
                    html,  # (optional) content
                    headers_dict)

                print("*" * 30)
                print(full_url, "served from cache file", file_name)
            else:
                # delete existing entries
                cursor.execute(
                    "DELETE FROM resource_location "
                    "WHERE `hashed_url` LIKE '%s'" %
                    (hashed_url)
                )
                os.remove(file_path + '.h')
                os.remove(file_path + '.c')
        elif js_tool:
            full_url = flow.request.pretty_url.split("?")[0]
            hashed_url = hashlib.sha256(full_url.encode()).hexdigest()
            cursor.execute(
                "SELECT `file_name` FROM resource_location "
                "WHERE `hashed_url` LIKE '%s'" %
                (hashed_url)
            )
            result = cursor.fetchone()
            if result:
                # Add version with scripts removed to cache
                file_name = str(result[0])
                file_path = self.path + "/cache/" + file_name
                with open(file_path + '.h', 'rb') as temp_file:
                    temp_headers = pickle.load(temp_file)

                headers_dict = {}
                for attr in list(temp_headers):
                    headers_dict[attr] = temp_headers[attr]

                with open(file_path + '.c', 'rb') as temp_file:
                    temp_content = pickle.load(temp_file)

                html = str(BeautifulSoup(temp_content, 'html.parser'))
                cnt = 1
                while "<script" in html:
                    html = html.replace(
                        "<script", "\n<!--script" + str(cnt) + "\n", 1)
                    html = html.replace("</script>", "\n-->\n", 1)
                    print("cnt =", cnt)
                    cnt += 1

                # return response
                flow.response = http.HTTPResponse.make(
                    200,  # (optional) status code
                    html,  # (optional) content
                    headers_dict)

                # add to database
                full_url += "?JSTool"
                hashed_url = hashlib.sha256(full_url.encode()).hexdigest()
                file_name = self.random_filename()
                file_path = self.path + "/cache/" + file_name
                cursor.execute(
                    "INSERT INTO resource_location "
                    "(`hashed_url`, `full_url`, `file_name`, datetime) "
                    "VALUES ('%s', '%s', '%s', NOW())" %
                    (hashed_url, full_url, file_name)
                )
                self.cnx.commit()

                # write to file
                with open(file_path + '.h', 'wb') as temp_file:
                    pickle.dump(flow.response.headers, temp_file)

                with open(file_path + '.c', 'wb') as temp_file:
                    pickle.dump(flow.response.content, temp_file)

        cursor.close()

    def response(self, flow: http.HTTPFlow):
        """Handle HTTP response."""
        full_url = flow.request.pretty_url.split("?")[0]
        if "?JSTool=" in flow.request.pretty_url:
            full_url += "?JSTool=" + \
                flow.request.pretty_url.split("?JSTool=")[-1]
        hashed_url = hashlib.sha256(full_url.encode()).hexdigest()
        cursor = self.cnx.cursor()
        cursor.execute(
            "SELECT `file_name` FROM resource_location "
            "WHERE `hashed_url` LIKE '%s'" %
            (hashed_url)
        )
        result = cursor.fetchone()
        if not result:
            # not yet in db
            file_name = self.random_filename()
            file_path = self.path + "/cache/" + file_name
            cursor.execute(
                "INSERT INTO resource_location "
                "(`hashed_url`, `full_url`, `file_name`, datetime) "
                "VALUES ('%s', '%s', '%s', NOW())" %
                (hashed_url, full_url, file_name)
            )
            self.cnx.commit()
            with open(file_path + '.h', 'wb') as temp_file:
                pickle.dump(flow.response.headers, temp_file)
            with open(file_path + '.c', 'wb') as temp_file:
                pickle.dump(flow.response.content, temp_file)
        cursor.close()

# pylint: disable=invalid-name
addons = [LocalCache()]
