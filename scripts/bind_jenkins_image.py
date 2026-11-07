#!/usr/bin/env python3
"""Bind an explicitly built local candidate to the selected Compose runtime by immutable ID."""
import argparse,json,re,subprocess
from compose_runtime import update_context

def verified_image_id(reference):
    records=json.loads(subprocess.check_output(['docker','image','inspect',reference],text=True))
    if len(records)!=1:raise RuntimeError('An exact local Jenkins candidate image is required')
    image=records[0];image_id=image['Id'];labels=image.get('Config',{}).get('Labels') or {}
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',image_id) or labels.get('io.dateninfrastruktur.delivery.provenance')!='1':
        raise RuntimeError('Build the Jenkins CSV candidate from the sibling checkouts first')
    return image_id

def bind(context,reference):
    context.verify_project()
    image_id=verified_image_id(reference)
    return update_context(context,{'JENKINS_IMAGE':image_id,'DI_JENKINS_IMAGE_SHA256':image_id.split(':',1)[1]})

if __name__=='__main__':
    from compose_operations import resolve
    p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--env');p.add_argument('--project');a=p.parse_args()
    context=bind(resolve(a.env,a.project),a.image)
    print('Jenkins candidate bound: '+context.values['JENKINS_IMAGE'])
