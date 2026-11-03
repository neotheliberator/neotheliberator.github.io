"""Publish explicitly selected public files with pinned SSH identity and backups.

Connection settings and password come only from protected environment secrets.
This never mirrors or deletes other remote files. Backups contain only bytes
already verified to be publicly available at the corresponding HTTPS URL.
"""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
import uuid

import paramiko

LIMIT = 10 * 1024 * 1024
EXTENSIONS = {'.html', '.css', '.js', '.json', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.ico', '.woff', '.woff2'}
SOURCE = Path('nebukad').resolve()
BACKUP = Path('deployment-backup')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected_files(raw):
    names = shlex.split(raw)
    if not names or len(names) > 30 or len(set(names)) != len(names):
        raise ValueError('Select between 1 and 30 distinct files')
    result = {}
    for name in names:
        p = PurePosixPath(name)
        if (p.is_absolute() or '\\' in name or p.as_posix() != name
                or any(part.startswith('.') for part in p.parts)
                or p.suffix.lower() not in EXTENSIONS):
            raise ValueError('Invalid static file path')
        local = SOURCE / name
        if not local.resolve().is_relative_to(SOURCE) or local.is_symlink():
            raise ValueError('Source must remain inside the website folder')
        data = local.read_bytes()
        if not data or len(data) > LIMIT:
            raise ValueError('Selected file is empty or too large')
        result[name] = data
    return result


class PinnedHost(paramiko.MissingHostKeyPolicy):
    def __init__(self, expected):
        self.expected = expected

    def missing_host_key(self, client, hostname, key):
        actual = 'SHA256:' + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
        if actual != self.expected:
            raise paramiko.SSHException('SSH host identity did not match the verified provider fingerprint')


def connect(config):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(PinnedHost(config['fingerprint']))
    client.connect(config['host'], port=int(config['port']), username=config['user'],
                   password=os.environ['IONOS_SFTP_PASSWORD'], allow_agent=False,
                   look_for_keys=False, timeout=30, banner_timeout=30, auth_timeout=30)
    return client


def remote_bytes(sftp, name):
    try:
        info = sftp.lstat(name)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
        raise ValueError('Existing destination is not a permitted regular file')
    with sftp.open(name, 'rb') as handle:
        data = handle.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('Destination exceeds size limit')
    return data


def public_bytes(config, name, nonce):
    url = config['base_url'].rstrip('/') + '/' + quote(name, safe='/') + '?deployment=' + nonce
    with urlopen(Request(url, headers={'Cache-Control': 'no-cache'}), timeout=30) as response:
        if urlsplit(response.url).netloc != urlsplit(config['base_url']).netloc:
            raise ValueError('Public verification redirected to another host')
        data = response.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('Public response exceeds size limit')
    return data


def backup(sftp, config, files):
    BACKUP.mkdir(exist_ok=False)
    manifest = {}
    for name, new in files.items():
        old = remote_bytes(sftp, name)
        if old is not None:
            # Never put non-public server configuration into a CI artifact.
            if public_bytes(config, name, uuid.uuid4().hex) != old:
                raise ValueError('Remote content differs from public content; backup and deployment stopped')
            destination = BACKUP / 'files' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(old)
        manifest[name] = {'before': None if old is None else digest(old), 'after': digest(new)}
    (BACKUP / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('SFTP authentication and pinned host identity verified; selected-file backup complete.')


def publish(sftp, config, files):
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    if set(manifest) != set(files):
        raise ValueError('Selection differs from backed-up selection')
    for name, data in files.items():
        old = remote_bytes(sftp, name)
        before = None if old is None else digest(old)
        if before != manifest[name]['before'] or digest(data) != manifest[name]['after']:
            raise ValueError('Source or destination changed after backup; stopped')
    for name, data in files.items():
        parent = PurePosixPath(name).parent
        # Parent folders must already exist, so no implicit expansion of scope.
        if parent.as_posix() != '.':
            sftp.stat(parent.as_posix())
        temporary = str(parent / ('upload-' + uuid.uuid4().hex + '.tmp'))
        try:
            with sftp.open(temporary, 'wxb') as handle:
                handle.write(data)
            sftp.chmod(temporary, 0o644)
            if remote_bytes(sftp, temporary) != data:
                raise ValueError('Transferred bytes did not match')
            try:
                sftp.posix_rename(temporary, name)
            except OSError:
                if manifest[name]['before'] is not None:
                    raise
                sftp.rename(temporary, name)
        finally:
            try:
                sftp.remove(temporary)
            except FileNotFoundError:
                pass
        for attempt in range(6):
            try:
                if public_bytes(config, name, uuid.uuid4().hex) == data:
                    break
            except HTTPError as error:
                if error.code not in (404, 502, 503, 504):
                    raise
            if attempt == 5:
                raise ValueError('Public verification failed; inspect the preserved backup before retrying')
            time.sleep(5)
        print('Published and verified: ' + name + ' SHA256 ' + digest(data))


def main():
    config = json.loads(os.environ['IONOS_CONNECTION_JSON'])
    if urlsplit(config['base_url']).scheme != 'https':
        raise ValueError('Public verification requires HTTPS')
    files = selected_files(os.environ['DEPLOY_FILES'])
    with connect(config) as client, client.open_sftp() as sftp:
        if sys.argv[1] == 'backup':
            backup(sftp, config, files)
        elif sys.argv[1] == 'publish':
            publish(sftp, config, files)
        else:
            raise ValueError('Unknown deployment phase')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never include connection configuration or credentials in public logs.
        print('Deployment stopped: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
