import os
import re
import subprocess


STACK_TAG = re.compile(
    rb'(?m)^([ \t]*"image": "\$\{[A-Z_]+:-ghcr\.io/sogis/dateninfrastruktur-'
    rb'(?:admin|jenkins|postgres|superset|tools):)[\w][\w.-]{0,127}(\}",?)$'
)


def only_stack_tags_changed(before, after):
    if subprocess.run(
        ['git', 'cat-file', '-e', f'{before}^{{commit}}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode:
        return False
    changed = subprocess.check_output(['git', 'diff', '--name-only', '-z', before, after, '--'])
    if changed != b'compose.yaml\0':
        return False
    if subprocess.check_output(['git', 'diff', '--summary', before, after, '--', 'compose.yaml']):
        return False

    old = subprocess.check_output(['git', 'show', f'{before}:compose.yaml'])
    new = subprocess.check_output(['git', 'show', f'{after}:compose.yaml'])
    return old != new and STACK_TAG.sub(rb'\1<TAG>\2', old) == STACK_TAG.sub(rb'\1<TAG>\2', new)


if __name__ == '__main__':
    skip = only_stack_tags_changed(os.environ['PUSH_BEFORE'], os.environ['GITHUB_SHA'])
    if skip:
        print('Only default Stack image tags changed. Skipping the release build.')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        print(f'release={str(not skip).lower()}', file=output)
