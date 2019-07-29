#!/usr/bin/env python

import sys, os, aiml, re, shutil, json, urllib, BaseHTTPServer

BRAIN_FILE="brain.dump"

reload(sys)

sys.setdefaultencoding('utf8')

siri = aiml.Kernel()

if os.path.exists(BRAIN_FILE):
    print("Load brain file: " + BRAIN_FILE)
    siri.loadBrain(BRAIN_FILE)
else:
    print("Learn AIML files")
    siri.bootstrap(learnFiles="std-startup.aiml", commands="load aiml b")
    print("Saving brain file: " + BRAIN_FILE)
    siri.saveBrain(BRAIN_FILE)

def get_answer(handler):
    question = handler.path[10:].split("/",1)[0]
    question = urllib.unquote(question)
    answer = siri.respond(question)
    if answer == "":
        answer = "I couldn't understand what you said! Would you like to repeat?"
    resp = {
        "status":"success",
        "data":answer,
        "msg":question
    }
    return resp

#curl -X PUT -d '{"pattern": "HI SIRI","template":"Hello sir"}' "http://localhost:8800/learn/"
def siri_learn(handler):
    key = urllib.unquote(handler.path[7:])
    payload = handler.get_payload()
    resp = {
        "status":"success",
        "data":payload,
        "msg":"Siri learned"
    }
    return resp

def no_route(handler):
    resp = {
        "status":"error",
        "data":None,
        "msg":"Sorry, i can't hear from you !"
    }
    return resp

class SiriHandle(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routes = {
            r'^/$' : {
                'GET' : no_route,
                'media_type':'application/json'
            },
            r'^/question/([^/]+)?':{
                'GET':get_answer,
                'media_type':'application/json'
            },
            r'^/learn/':{
                'PUT':siri_learn,
                'media_type':'application/json'
            }
        }
        return BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_HEAD(self):
        self.handle_method('HEAD')

    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')

    def get_payload(self):
        payload_len = int(self.headers.getheader('content-length', 0))
        payload = self.rfile.read(payload_len)
        payload = json.loads(payload)
        return payload

    def get_route(self):
        for path, route in self.routes.iteritems():
            if re.match(path, self.path):
                return route
        return None

    def handle_method(self, method):
        route = self.get_route()
        if route is None:
            self.send_response(404)
            self.end_headers()
            resp = no_route()
            self.wfile.write(json.dumps(resp))
        else:
            if method == 'HEAD':
                self.send_response(200)
                if 'media_type' in route:
                    self.send_header('Content-Type',route['media_type'])
                self.end_headers()
            else:
                if method in route:
                    resp = route[method](self)
                    self.send_response(200)
                    if 'media_type' in route:
                        self.send_header('Content-Type', route['media_type'])
                    self.end_headers()
                    self.wfile.write(json.dumps(resp))
                else:
                    resp = no_route()
                    self.send_response(405)
                    self.end_headers()
                    self.wfile.write(json.dumps(resp))

def siri_server(port):
    http_server = BaseHTTPServer.HTTPServer(('',port), SiriHandle)
    print 'Start AIML server at port %d' % port
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    print 'Stopping HTTP server'
    http_server.server_close()

def main(argv):
    siri_server(8800)

if __name__ == '__main__':
    main(sys.argv[1:])