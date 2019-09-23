#!/usr/bin/env python2
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse, urlunparse, ParseResult
from SocketServer import ThreadingMixIn
from socket import error as SocketError
from httplib import HTTPResponse
from tempfile import gettempdir
from os import path, listdir
from ssl import wrap_socket
from socket import socket
from re import compile
from sys import argv
from bs4 import BeautifulSoup
from anytree import Node, RenderTree
from collections import Counter, OrderedDict, defaultdict
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import errno
import thread
import os 
import signal
import sys

import time 
from OpenSSL.crypto import (X509Extension, X509, dump_privatekey, dump_certificate, load_certificate, load_privatekey,
							PKey, TYPE_RSA, X509Req)
from OpenSSL.SSL import FILETYPE_PEM

# import gzip
# import StringIO
# import zlib
# import brotli
# import shutil
import binascii
import jsbeautifier
import pymysql

http_proxy  = "http://127.0.0.1:9999"
https_proxy = "https://127.0.0.1:9999"
proxy_data_path = "data/"

# check if the data folder exists
if not os.path.exists("data"):
	os.system("mkdir data")

# read DB user name and password
db_name = "JSCleaner"
db_user = "root"
db_password = raw_input ("please enter DB password ")

# def decode_gzip(filepath):
# 	print "Trying to decode: " + filepath

# 	f = open (filepath + ".c", "rb")
# 	content = f.read()
# 	data = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(content))
# 	data = data.read()
# 	print "gzip content is decoded"
# 	return data

# def get_content_encoding(filepath):
# 	print "Getting Content-Encoding....."
# 	with open(filepath + ".h") as f:
# 		encoding = ""
# 		for line in f:
# 			if "Content-Encoding:" in line:
# 				encoding = line.split(' ',1)[1]
# 				print "Content-Encoding: " + encoding
# 				return encoding


# def decode_br_content(filepath):
# 	print "Trying to decode: " + filepath

# 	f = open (filepath + ".c", "rb")
# 	content = f.read()
# 	decoded_content = brotli.decompress(content)
# 	print "br Content is decoded"
# 	return decoded_content


# def encode_save_index(content, original_name, new_name):
# 	#Saving encoded new file to the proxy
# 	#Note: new name should be without extention
# 	try:
# 		with gzip.open(proxy_data_path + new_name + ".c", "wb") as f:
# 			f.write(content)
# 			f.close
# 			print "HTML is encoded and saved!"
# 	except Exception,e: 
# 		print "HTML cannot be encoded! " + str(e)
# 		exit()


# 	#Copying headers from the proxy in another file.....
# 	shutil.copy(original_name + ".h",proxy_data_path + new_name + ".h")
# 	#Changing content-length according to the saved .c
# 	content_size = os.path.getsize(proxy_data_path + new_name + ".c")
# 	print "This is the new size" 
# 	print content_size
	
# 	print "Updating header with the new size....."

# 	with open(proxy_data_path + new_name + ".h") as f:
# 		new_text = ""
# 		existing_size = ""
# 		for line in f:
# 			if "Content-Length:" in line:
# 				existing_size = line.split(' ',1)[1]
# 				print "line:" + line + " with existing size " + str(existing_size) + " should be replaced by: " + str(content_size)
	
# 	if(existing_size != ""):
# 		with open(proxy_data_path + new_name + ".h") as f:
# 			atext = f.read().replace(existing_size, str(content_size)+ "\n")

# 		with open(proxy_data_path + new_name + ".h", "w") as f:
# 			f.write(atext)


class CertificateAuthority(object):

	def __init__(self, ca_file='ca-local.pem', cache_dir=gettempdir()):
		self.ca_file = ca_file
		self.cache_dir = cache_dir
		self._serial = self._get_serial()
		if not path.exists(ca_file):
			self._generate_ca()
		else:
			self._read_ca(ca_file)

	def _get_serial(self):
		s = 1
		for c in filter(lambda x: x.startswith('.pymp_'), listdir(self.cache_dir)):
			c = load_certificate(FILETYPE_PEM, open(path.sep.join([self.cache_dir, c])).read())
			sc = c.get_serial_number()
			if sc > s:
				s = sc
			del c
		return s

	def _generate_ca(self):
		# Generate key
		self.key = PKey()
		self.key.generate_key(TYPE_RSA, 2048)

		# Generate certificate
		self.cert = X509()
		self.cert.set_version(3)
		self.cert.set_serial_number(1)
		self.cert.get_subject().CN = 'ca.mitm.com'
		self.cert.gmtime_adj_notBefore(0)
		self.cert.gmtime_adj_notAfter(315360000)
		self.cert.set_issuer(self.cert.get_subject())
		self.cert.set_pubkey(self.key)
		self.cert.add_extensions([
			X509Extension("basicConstraints", True, "CA:TRUE, pathlen:0"),
			X509Extension("keyUsage", True, "keyCertSign, cRLSign"),
			X509Extension("subjectKeyIdentifier", False, "hash", subject=self.cert),
			])
		self.cert.sign(self.key, "sha1")

		with open(self.ca_file, 'wb+') as f:
			f.write(dump_privatekey(FILETYPE_PEM, self.key))
			f.write(dump_certificate(FILETYPE_PEM, self.cert))

	def _read_ca(self, file):
		self.cert = load_certificate(FILETYPE_PEM, open(file).read())
		self.key = load_privatekey(FILETYPE_PEM, open(file).read())

	def __getitem__(self, cn):
		cnp = path.sep.join([self.cache_dir, '.pymp_%s.pem' % cn])
		if not path.exists(cnp):
			# create certificate
			key = PKey()
			key.generate_key(TYPE_RSA, 2048)

			# Generate CSR
			req = X509Req()
			req.get_subject().CN = cn
			req.set_pubkey(key)
			req.sign(key, 'sha1')

			# Sign CSR
			cert = X509()
			cert.set_subject(req.get_subject())
			cert.set_serial_number(self.serial)
			cert.gmtime_adj_notBefore(0)
			cert.gmtime_adj_notAfter(31536000)
			cert.set_issuer(self.cert.get_subject())
			cert.set_pubkey(req.get_pubkey())
			cert.sign(self.key, 'sha1')

			with open(cnp, 'wb+') as f:
				f.write(dump_privatekey(FILETYPE_PEM, key))
				f.write(dump_certificate(FILETYPE_PEM, cert))

		return cnp

	@property
	def serial(self):
		self._serial += 1
		return self._serial


class UnsupportedSchemeException(Exception):
	pass


class ProxyHandler(BaseHTTPRequestHandler):

	r = compile(r'http://[^/]+(/?.*)(?i)')

	def __init__(self, request, client_address, server):
		#print 'request' + request
		self.is_connect = False
		self.rtt = float(0.0000000)

		try:
			BaseHTTPRequestHandler.__init__(self, request, client_address, server)
		except Exception, e:
			pass

	def _connect_to_host(self):
		# Get hostname and port to connect to
		if self.is_connect:
			self.hostname, self.port = self.path.split(':')		
		else:	
			u = urlparse(self.path)
			if u.scheme != 'http':
				raise UnsupportedSchemeException('Unknown scheme %s' % repr(u.scheme))
			self.hostname = u.hostname
			self.port = u.port or 80
			self.path = urlunparse(
				ParseResult(
					scheme='',
					netloc='',
					params=u.params,
					path=u.path or '/',
					query=u.query,
					fragment=u.fragment
				)
			)

		# Connect to destination
		self._proxy_sock = socket()
		self._proxy_sock.settimeout(10)
		a = time.time()
		self._proxy_sock.connect((self.hostname, int(self.port)))
		self.rtt = float(time.time() - a)
		# Wrap socket if SSL is required
		if self.is_connect:
			self._proxy_sock = wrap_socket(self._proxy_sock)



	def _transition_to_ssl(self):
		self.request = wrap_socket(self.request, server_side=True, certfile=self.server.ca[self.path.split(':')[0]])


	def do_CONNECT(self):

		# print '--req-- '+ self.path

		self.is_connect = True
		
		try:
			# Connect to destination first
			self._connect_to_host()
			# If successful, let's do this!
			self.send_response(200, 'Connection established')
			self.end_headers()
			#self.request.sendall('%s 200 Connection established\r\n\r\n' % self.request_version)
			self._transition_to_ssl()
		
		except Exception, e:
			# print "exception "

			self.send_response(200, 'Connection established')
			self.end_headers()
			#self.request.sendall('%s 200 Connection established\r\n\r\n' % self.request_version)
			self._transition_to_ssl()
			#self.send_error(500, str(e))
			#return

		# Reload!
		self.setup()
		self.ssl_host = 'https://%s' % self.path
		self.handle_one_request()
		
		#print "Hello server!" + self.ssl_host + "\n\n\n\n\n\n"	

	#By Moumena: Request, Response
	def do_COMMAND(self):
		h = None

		try:
			url_requested = self.ssl_host + self.path
		except:
			url_requested = self.path

		# Connect to the database.
		conn = pymysql.connect(db=db_name,user=db_user,passwd=db_password,host='localhost',autocommit=True)
		d = conn.cursor()

		sql = "SELECT filename FROM caching WHERE url='{0}'".format(url_requested.replace(":443",""))
		d.execute(sql)

		num = d.rowcount

		if num > 0:
			filename = d.fetchone()[0]
		else:
			filename = ""

		d.close()
		conn.close()


		if num > 0:
			# filename = d.fetchone()[0]
			print "CACHE HIT ..... ", filename

			f = open (proxy_data_path+filename+".h", "r")
			res = f.read()
			f.close()
			f = open (proxy_data_path+filename+".c", "r")
			res += f.read()
			f.close()

			self.request.sendall(self.mitm_response(res))
			self._proxy_sock.close()
			return

		#Comment the following else if you would like to clone new pages
		#Uncomment the following else if you would like to retrieve existing pages
		# else:
		# 	print '--- Empty: '+ url_requested[:50]

		# 	f = open ("empty.h", "r")
		# 	res = f.read()
		# 	f.close()

		# 	self.request.sendall(self.mitm_response(res))
		# 	self._proxy_sock.close()
		# 	return

		if not self.is_connect:
			try:
				# Connect to destination
				self._connect_to_host()
			except Exception, e:
				self.send_error(500, str(e))
				return

		req = '%s %s %s\r\n' % (self.command, self.path, self.request_version)
		req += '%s\r\n' % self.headers

		# Append message body if present to the request
		if 'Content-Length' in self.headers:
			req += self.rfile.read(int(self.headers['Content-Length']))

		try:
			# Send it down the pipe!
			self._proxy_sock.sendall(self.mitm_request(req))

			# Parse response
			h = HTTPResponse(self._proxy_sock)
			h.begin()
			# Get rid of the pesky header
			del h.msg['Transfer-Encoding']

			# Time to relay the message across
			res = '%s %s %s\r\n' % (self.request_version, h.status, h.reason)
			res += '%s\r\n' % h.msg

			res_headers = res
			content_received = h.read()

			res += content_received
			
			try:
				name = url_requested

				print '**response** '+ url_requested[:50]

				name = binascii.b2a_hex(os.urandom(15))
				while os.path.exists("./data/"+name):
					name = binascii.b2a_hex(os.urandom(15))

				# Connect to the database.
				conn = pymysql.connect(db=db_name,user=db_user,passwd=db_password,host='localhost',autocommit=True)
				c = conn.cursor()
				sql = "INSERT INTO caching (url, filename) VALUES (%s,%s)"
				c.execute(sql, (url_requested.replace(":443",""), name))
				c.close()
				conn.close()


				f = open("data/"+name+".h","w")
				f.write(res_headers)
				f.close()

				f = open("data/"+name+".c","w")
				f.write(content_received)
				f.close()

			except Exception as e:
				print "error:", e, url_requested[:50], name

			self.request.sendall(self.mitm_response(res))

		except SocketError as e:
			if e.errno != errno.ECONNRESET:
				raise
			pass

		# Let's close off the remote end
		if h != None:
			h.close()
		self._proxy_sock.close()


	def log_message (self, format, *args):
		return

	def mitm_request(self, data):
		for p in self.server._req_plugins:
			data = p(self.server, self).do_request(data)
		return data

	def mitm_response(self, data):
		for p in self.server._res_plugins:
			data = p(self.server, self).do_response(data)
		return data

	def __getattr__(self, item):
		if item.startswith('do_'):
			return self.do_COMMAND


class InterceptorPlugin(object):

	def __init__(self, server, msg):
		self.server = server
		self.message = msg

class RequestInterceptorPlugin(InterceptorPlugin):
	def do_request(self, data):
		return data


class ResponseInterceptorPlugin(InterceptorPlugin):

	def do_response(self, data):
		return data


class InvalidInterceptorPluginException(Exception):
	pass


class MitmProxy(HTTPServer):

	def __init__(self, server_address=('', 9999), RequestHandlerClass=ProxyHandler, bind_and_activate=True, ca_file='ca-local.pem'):
		HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
		self.ca = CertificateAuthority(ca_file)
		self._res_plugins = []
		self._req_plugins = []

	def register_interceptor(self, interceptor_class):
		if not issubclass(interceptor_class, InterceptorPlugin):
			raise InvalidInterceptorPluginException('Expected type InterceptorPlugin got %s instead' % type(interceptor_class))
		if issubclass(interceptor_class, RequestInterceptorPlugin):
			self._req_plugins.append(interceptor_class)
		if issubclass(interceptor_class, ResponseInterceptorPlugin):
			self._res_plugins.append(interceptor_class)


class AsyncMitmProxy(ThreadingMixIn, MitmProxy):
	pass


class MitmProxyHandler(ProxyHandler):

	def mitm_request(self, data):
		# print '>> %s' % repr(data[:100])
		return data

	def mitm_response(self, data):
		# print '<< %s' % repr(data[:100])
		return data


class DebugInterceptor(RequestInterceptorPlugin, ResponseInterceptorPlugin):

		def do_request(self, data):
			return data

		def do_response(self, data):
			return data

if __name__ == '__main__':
	proxy = None

	if not argv[1:]:
		proxy = AsyncMitmProxy()
	else:
		proxy = AsyncMitmProxy(ca_file=argv[1])
	proxy.register_interceptor(DebugInterceptor)

	try:
		proxy.serve_forever()
		
	except KeyboardInterrupt:
		proxy.server_close()
