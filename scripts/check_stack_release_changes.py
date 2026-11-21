import os
import re
import subprocess


STACK_IMAGE = rb'ghcr\.io/sogis/dateninfrastruktur-(?:admin|jenkins|postgres|superset|tools)'
TAG = rb'[\w][\w.-]{0,127}'
COMPOSE_TAG = re.compile(
    rb'(?m)^([ \t]*"image": "\$\{[A-Z_]+:-' + STACK_IMAGE + rb':)' + TAG + rb'(\}",?)$'
)
PUBLISHED_IMAGES = re.compile(rb'(?ms)^PUBLISHED_IMAGES = \{\n.*?^\}')
HOST_TAG = re.compile(
    rb"(?m)^([ \t]*'(?:ADMIN_IMAGE|JENKINS_IMAGE|POSTGRES_IMAGE|SUPERSET_IMAGE|TOOL_IMAGE)': '"
    + STACK_IMAGE + rb":)" + TAG + rb"(',)$"
)
COMPOSE_PATH = b'compose.yaml'
RUNTIME_PATH = b'scripts/compose_runtime.py'


def without_stack_tags(path, content):
    replacement = rb'\1<TAG>\2'
    if path == COMPOSE_PATH:
        return COMPOSE_TAG.sub(replacement, content)
    return PUBLISHED_IMAGES.sub(lambda block: HOST_TAG.sub(replacement, block[0]), content)


def only_docs_or_stack_tags_changed(before, after):
    if subprocess.run(
        ['git', 'cat-file', '-e', f'{before}^{{commit}}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode:
        return False
    names = subprocess.check_output(['git', 'diff', '--no-renames', '--name-only', '-z', before, after, '--'])
    if not names:
        return False

    for path in names.rstrip(b'\0').split(b'\0'):
        if path == b'README.md' or (path.startswith(b'docs/') and path.endswith(b'.md')):
            continue
        if path not in (COMPOSE_PATH, RUNTIME_PATH):
            return False
        path_text = path.decode('ascii')
        if subprocess.check_output(['git', 'diff', '--summary', before, after, '--', path_text]):
            return False
        old = subprocess.check_output(['git', 'show', f'{before}:{path_text}'])
        new = subprocess.check_output(['git', 'show', f'{after}:{path_text}'])
        if old == new or without_stack_tags(path, old) != without_stack_tags(path, new):
            return False
    return True


if __name__ == '__main__':
    skip = only_docs_or_stack_tags_changed(os.environ['PUSH_BEFORE'], os.environ['GITHUB_SHA'])
    if skip:
        print('Only documentation or default Stack image tags changed. Skipping the release build.')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        print(f'release={str(not skip).lower()}', file=output)
