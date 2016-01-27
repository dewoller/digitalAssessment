#!/usr/bin/env python
#    --notebook-dir=/pandas/notebooks

"""Simple HTTP Server With Upload.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""


__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = "http://luy.li/"

import os
import posixpath
from http.server import BaseHTTPRequestHandler,HTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
import tempfile
import processFile
import databaseConnection
db = databaseConnection.databaseConnection()

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Mark Coding Assignments</title>\n" )
        f.write("<body>\n<h2>Mark Coding Assignments</h2>\n" )
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        id=db.getPersistant()
        f.write("""Assignment ID:        <input name="id" type="text" value="{id}"/> <br/>"""
                .format( id=id ))
        f.write("Answer file name    : <input name=\"a\" type=\"file\"/> <br/>")
        f.write("Submission file name: <input name=\"s\" type=\"file\"/> <br/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
        f.close()


    def getInputFiles( self ):
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        parm={}
        fd, parm['s'] = tempfile.mkstemp(".zip")
        os.write(fd, form['s'].file.read())
        os.close( fd )
        fd, parm['a'] = tempfile.mkstemp(".xlsx")
        os.write(fd, form['a'].file.read())
        os.close(fd)
        parm[ 'id' ] = form['id'].value
        db.setPersistant( parm[ 'id' ]) 
        return ( parm )

        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                self.wfile.write('\tUploaded %s as "%s" (%d bytes)\n' % \
                        (field, field_item.filename, file_len))
            else:
                # Regular form value
                self.wfile.write('\t%s=%s\n' % (field, form[field].value))


    def do_POST(self):
        # Parse the form data posted
        # get the files
        # process the files
        # return the results
        # Begin the response
        parm = self.getInputFiles()
        (fd, outputFile)=tempfile.mkstemp(".zip")
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            processFile.processSubmissionZip( parm['a'], parm['s'], outputFile )
            os.close(fd)
            f=open(outputFile, "rb")
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", "application/zip")
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
        f.close()
        return



if __name__ == '__main__':
    try:
        # Create a web server and define the handler to manage the
        # incoming request
        server = HTTPServer(('', 8888), SimpleHTTPRequestHandler)
        print ('Started httpserver on port ' , 8888)

        # Wait forever for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        print ('^C received, shutting down the web server')
        server.socket.close()

