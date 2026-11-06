#!/usr/bin/env python3
"""A route may converge after outage; denials and data corruption may not pass."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import test_architecture_flows as flows


class RecoveryTest(unittest.TestCase):
    def probe(self,responses,*,recover=True,origin_on_denial=False):
        state={};calls=[]
        def http(*args,**kwargs):
            index=min(len(calls),len(responses)-1);status,body=responses[index];calls.append(status)
            state.update(probe='probe',status=str(status),origin='127.0.0.2:8080' if status==200 or origin_on_denial else '-')
            return status,{},body
        context=SimpleNamespace(values={'GATEWAY_PORT':'1'},runtime='synthetic',
            command=lambda *args,**kwargs:SimpleNamespace(stdout=json.dumps(state)))
        ticks=iter(range(0,10000,2))
        with patch.object(flows,'http',side_effect=http),patch.object(flows,'uuid4',return_value='probe'), \
             patch.object(flows,'origin_address',return_value='127.0.0.2:8080'), \
             patch('delivery_queue_harness.time.sleep'),patch('delivery_queue_harness.time.monotonic',side_effect=lambda:next(ticks)):
            flows.download(context,'/synthetic',200,body=b'file',recover=recover)
        return calls

    def test_transient_denial_converges_with_correct_bytes_and_origin(self):
        self.assertEqual(self.probe([(503,b''),(200,b'file')]),[503,200])
    def test_regular_download_does_not_retry(self):
        with self.assertRaises(AssertionError):self.probe([(503,b''),(200,b'file')],recover=False)
    def test_permanent_failure_is_not_pass(self):
        with self.assertRaisesRegex(RuntimeError,'Timed out'):self.probe([(503,b'')])
    def test_permission_denial_is_not_retried(self):
        with self.assertRaises(AssertionError):self.probe([(403,b''),(200,b'file')])
    def test_transient_denial_cannot_reach_origin(self):
        with self.assertRaisesRegex(AssertionError,'reached'):self.probe([(503,b'')],origin_on_denial=True)
    def test_failure_cannot_deliver_file(self):
        with self.assertRaises(AssertionError):self.probe([(503,b'file')])
    def test_success_requires_exact_file(self):
        with self.assertRaises(AssertionError):self.probe([(200,b'wrong')])


if __name__=='__main__':unittest.main()
