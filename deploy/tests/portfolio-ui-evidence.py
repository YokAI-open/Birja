#!/usr/bin/env python3
"""Capture actual Phase13 UI; package inert synthetic DOM with current-source proof."""
import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 375, 768, 1024, 1280, 1440)
STATES = ('overview', 'create-long-astral', 'keyboard-error-focus', 'unknown',
          'edit', 'stale-draft', 'switch', 'incomplete', 'failed-refresh', 'cap', 'empty', 'error')
HASH = re.compile(r'^[0-9a-f]{64}$')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def source_snapshot():
    paths = set()
    for name in ('frontend/src', 'frontend/e2e', 'frontend/public', 'backend/app', 'backend/alembic'):
        paths.update(p for p in (ROOT / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update((ROOT / 'frontend/node_modules/@fontsource-variable/inter/files').glob('*.woff2'))
    paths.update((ROOT / 'frontend/node_modules/@fontsource-variable/inter').glob('*.css'))
    paths.update((ROOT / 'frontend').glob('tsconfig*.json'))
    for name in ('frontend/index.html', 'frontend/package.json', 'frontend/package-lock.json',
                 'frontend/vite.config.ts', 'frontend/playwright.config.ts', 'frontend/components.json', 'frontend/Dockerfile',
                 'backend/Dockerfile', 'backend/uv.lock', 'docker-compose.yml',
                 'deploy/tests/run-stock-browser.py', 'deploy/tests/portfolio-ui-evidence.py',
                 'deploy/tests/test-portfolio-ui-evidence.py'):
        paths.add(ROOT / name)
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError('Unsafe render input')
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}


def input_digest(source):
    return digest(json.dumps(source, sort_keys=True, separators=(',', ':')).encode())


def contract_example():
    """Independent schema specimen for offline negative tests, never a receipt."""
    source = {'frontend/src/App.tsx': 'a' * 64}
    return {'format': 1, 'phase': 13, 'synthetic': True, 'source_sha256': source,
            'git_commit': 'a' * 40, 'render_inputs_sha256': input_digest(source),
            'native_200_percent_verified': False, 'owner_accepted': False,
            'captures': [{'state': state, 'width': width, 'browser': 'chromium',
                          'browser_version': '1.2.3', 'scope': 'a' * 64,
                          'render_inputs_sha256': input_digest(source)}
                         for width in WIDTHS for state in STATES]}


def validate_manifest(value, *, source=None):
    if not isinstance(value, dict) or value.get('format') != 1 or value.get('phase') != 13:
        raise ValueError('Unknown evidence format')
    if value.get('synthetic') is not True or value.get('native_200_percent_verified') is not False or value.get('owner_accepted') is not False:
        raise ValueError('Separate owner/native200 gates must remain pending')
    sources = value.get('source_sha256')
    if not isinstance(sources, dict) or not sources or any(not isinstance(k, str) or k.startswith('/') or '..' in Path(k).parts or not isinstance(v, str) or not HASH.fullmatch(v) for k, v in sources.items()):
        raise ValueError('Malformed source hashes')
    if source is not None and sources != source:
        raise ValueError('Source drift')
    bound = input_digest(sources)
    if value.get('render_inputs_sha256') != bound:
        raise ValueError('Render input mismatch')
    captures = value.get('captures')
    if not isinstance(captures, list) or len(captures) != len(WIDTHS) * len(STATES):
        raise ValueError('Incomplete capture matrix')
    found, scopes, browsers = set(), {}, set()
    for capture in captures:
        width, state = capture.get('width'), capture.get('state')
        if width not in WIDTHS or state not in STATES or (width, state) in found:
            raise ValueError('Unexpected or duplicate capture')
        found.add((width, state))
        scope = capture.get('scope')
        if not isinstance(scope, str) or not HASH.fullmatch(scope) or scopes.setdefault(width, scope) != scope:
            raise ValueError('Crossed owner capture')
        if capture.get('browser') != 'chromium' or not isinstance(capture.get('browser_version'), str) or not re.fullmatch(r'\d+(?:\.\d+){1,4}', capture['browser_version']):
            raise ValueError('Missing browser provenance')
        browsers.add((capture['browser'], capture['browser_version']))
        if capture.get('render_inputs_sha256') != bound:
            raise ValueError('Stale render capture')
    if len(browsers) != 1:
        raise ValueError('Mixed browser provenance')


def verify_artifacts(directory, hashes):
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError('No artifacts')
    for name, expected in hashes.items():
        path = directory / name
        if Path(name).name != name or path.is_symlink() or not path.is_file() or not HASH.fullmatch(expected) or digest(path.read_bytes()) != expected:
            raise ValueError('Missing/unsafe/tampered artifact: ' + name)


def validate_html(content):
    if re.search(r'<(?:script|form|iframe)\b|\s(?:src|href|action)=["\']https?:|bj_(?:access|refresh|csrf)\s*=', content, re.I):
        raise ValueError('Active/private capture')


def package(captured, destination, source, commit):
    if source_snapshot() != source:
        raise ValueError('Source changed during actual browser run')
    if destination.exists() or destination.is_symlink() or destination.with_suffix('.zip').exists():
        raise ValueError('Review destination already exists; preserve old packets')
    destination.mkdir(mode=0o700)
    bound, captures = input_digest(source), []
    for width in WIDTHS:
        for state in STATES:
            stem = f'phase13-{state}-{width}'
            text = (captured / (stem + '.html')).read_text()
            validate_html(text)
            match = re.search(r'<meta name="birja-evidence" content="([^"]+)">', text)
            if not match:
                raise ValueError('Missing browser capture metadata')
            metadata = json.loads(html.unescape(match[1]))
            if metadata.get('state') != state or metadata.get('width') != width or metadata.get('source') != commit or metadata.get('synthetic') is not True or metadata.get('native_200_percent_verified') is not False:
                raise ValueError('Capture state/source mismatch')
            captures.append({'state': state, 'width': width, 'browser': metadata['browser'],
                             'browser_version': metadata['version'], 'scope': metadata['scope'],
                             'render_inputs_sha256': bound})
            for suffix in ('.html', '.png'):
                path = captured / (stem + suffix)
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Missing actual browser artifact')
                (destination / path.name).write_bytes(path.read_bytes())
            if width >= 768:
                reflow = captured / (stem + '.reflow.png')
                if reflow.is_symlink() or not reflow.is_file():
                    raise ValueError('Missing actual narrow reflow screenshot')
                (destination / reflow.name).write_bytes(reflow.read_bytes())
            # Only allowlisted actual performance events, without request bodies,
            # headers, cookies, query strings, keys or private session storage.
            (destination / (stem + '.trace.json')).write_text(json.dumps(metadata['trace'], indent=2))
    manifest = {'format': 1, 'phase': 13, 'synthetic': True, 'git_commit': commit,
                'captured_at': datetime.now(UTC).isoformat(), 'source_sha256': source,
                'render_inputs_sha256': bound, 'native_200_percent_verified': False,
                'owner_accepted': False, 'captures': captures}
    links = ''.join(f'<li><a href="phase13-{state}-{width}.html">{state} at {width}px</a> · <a href="phase13-{state}-{width}.png">screenshot</a></li>' for width in WIDTHS for state in STATES)
    (destination / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Phase13 UI review</title><h1>Phase13 synthetic UI review</h1><p>Actual rendered read-only application states. Source hashes, browser version and credential-free performance traces are in manifest.json. Self-hosted fonts and CSS are embedded in each page. Owner acceptance and genuine desktop native 200% zoom remain PENDING Plan18. Viewport reflow is automated evidence only. Use your browser menu to inspect zoom and keyboard reachability.</p><ul>' + links + '</ul>')
    manifest['artifacts'] = {p.name: digest(p.read_bytes()) for p in sorted(destination.iterdir())}
    validate_manifest(manifest, source=source)
    verify_artifacts(destination, manifest['artifacts'])
    (destination / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2))
    archive = destination.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(destination.iterdir()):
            output.write(path, path.name)
            path.chmod(0o400)
    destination.chmod(0o500)
    print(json.dumps({'review': str(archive), 'sha256': digest(archive.read_bytes()),
                      'render_inputs_sha256': bound, 'captures': len(captures),
                      'artifacts': len(manifest['artifacts']), 'native_200_percent_verified': False}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path, help='Verify existing bundle directory against current render inputs')
    args = parser.parse_args()
    os.umask(0o077)
    if args.verify:
        value = json.loads((args.verify / 'manifest.json').read_text())
        validate_manifest(value, source=source_snapshot())
        verify_artifacts(args.verify, value['artifacts'])
        print('CURRENT SOURCE AND ARTIFACTS VERIFIED')
        return
    destination = Path('/tmp/birja-phase13-ui-review')
    if destination.exists() or destination.with_suffix('.zip').exists():
        raise ValueError('Preserve existing Phase13 packet before recapture')
    source = source_snapshot()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    captured = Path(tempfile.mkdtemp(prefix='birja-phase12-ui-review-p13-'))
    captured.rmdir()  # The owned browser runner requires an exclusive new path.
    subprocess.run(['python3', str(ROOT / 'deploy/tests/run-stock-browser.py'), '--suite', 'portfolios',
                    '--grep', 'Phase13', '--review-dir', str(captured)], cwd=ROOT, check=True)
    package(captured, destination, source, commit)


if __name__ == '__main__':
    main()
