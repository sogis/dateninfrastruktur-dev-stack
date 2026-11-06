#!/usr/bin/env python3
"""Bounded read recovery without replaying Keycloak mutations or refusals."""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import urllib.request

from provision_ingestion_oidc import call


class TransportTest(unittest.TestCase):
    def test_transport_contract(self):
        counts={}
        delay=time.sleep
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):self.respond()
            def do_POST(self):self.respond()
            def respond(self):
                counts[self.path]=counts.get(self.path,0)+1
                count=counts[self.path]
                if self.path in ('/permanent','/write') or self.path=='/recover' and count==1:
                    delay(.15)
                status=403 if self.path=='/forbidden' else 200
                data=b'broken-json' if self.path=='/malformed' else b'x'*524289 if self.path=='/oversize' else json.dumps({'verified':True}).encode()
                self.send_response(status);self.end_headers()
                try:self.wfile.write(data)
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        original=urllib.request.urlopen
        def bounded(request,timeout):
            self.assertEqual(timeout,20)
            return original(request,timeout=.04)
        try:
            with patch('provision_ingestion_oidc.urllib.request.urlopen',side_effect=bounded), patch('provision_ingestion_oidc.time.sleep'):
                base='http://127.0.0.1:'+str(server.server_port)
                self.assertEqual(call(base,'/recover'),{'verified':True})
                self.assertEqual(counts['/recover'],2)
                with self.assertRaisesRegex(RuntimeError,'after 3 attempt'):
                    call(base,'/permanent')
                self.assertEqual(counts['/permanent'],3)
                with self.assertRaisesRegex(RuntimeError,'after 1 attempt'):
                    call(base,'/write','POST',data={'operation':'synthetic'})
                self.assertEqual(counts['/write'],1)
                with self.assertRaisesRegex(RuntimeError,'HTTP 403'):call(base,'/forbidden')
                with self.assertRaises(json.JSONDecodeError):call(base,'/malformed')
                with self.assertRaisesRegex(RuntimeError,'too large'):call(base,'/oversize')
                for name in ('/forbidden','/malformed','/oversize'):self.assertEqual(counts[name],1)
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
