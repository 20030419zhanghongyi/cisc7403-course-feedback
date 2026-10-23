#!/usr/bin/env python3
"""Test the real three-container stack in a new, disposable Compose project.

Requires Docker Compose, Python 3 and free host ports 6110/6111. Creates its own
credentials, network and volume; only that randomly named project is removed.
"""
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SUCCESS = 'Feedback submitted successfully'
TOPICS = ['Virtual Machine', 'Docker', 'Kubernetes', 'Serverless']


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def http(port, data=None):
    payload = None if data is None else urlencode(data).encode()
    request = Request(f'http://127.0.0.1:{port}/', data=payload)
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.read().decode(), response.headers


def summary(total, average, counts):
    status, body, headers = http(6111)
    check(status == 200, 'Dashboard must return 200')
    check(f'id="total">{total}<' in body, 'Wrong total')
    check(f'id="average">{average}' in body, 'Wrong average')
    actual = re.findall(r'<tr><td>(.*?)</td><td>(\d+)</td></tr>', body)
    check(actual == list(zip(TOPICS, map(str, counts))), 'Wrong topic counts')
    check(headers['Cache-Control'] == 'no-store', 'Dashboard must refresh')


def main():
    for port in (6110, 6111):
        with socket.socket() as listener:
            listener.bind(('0.0.0.0', port))

    project = 'cisc7403-test-' + uuid.uuid4().hex[:12]
    environment = dict(os.environ, DB_HOST='db', DB_PORT='5432',
                       DB_NAME='course_feedback', DB_USER='course_app',
                       DB_PASSWORD=secrets.token_hex(24))
    with tempfile.TemporaryDirectory(prefix='cisc7403-test-') as directory:
        env_file = Path(directory) / '.env'
        env_file.write_text('')
        command = ['docker', 'compose', '--project-name', project,
                   '--env-file', str(env_file), '-f', str(ROOT / 'docker-compose.yml')]

        def compose(*args, stdin=None, capture=True, required=True):
            result = subprocess.run(command + list(args), cwd=ROOT, env=environment,
                                    input=stdin, text=True, capture_output=capture)
            if required and result.returncode:
                # Do not echo the environment or expanded Compose configuration.
                if capture:
                    print(result.stderr)
                raise RuntimeError(f'Compose {args[0]} failed ({result.returncode})')
            return result

        def sql(statement, required=True):
            return compose('exec', '-T', 'db', 'sh', '-c',
                           'psql -v ON_ERROR_STOP=1 -At -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
                           stdin=statement, required=required)

        def count():
            return int(sql('SELECT COUNT(*) FROM public.feedback;').stdout.strip())

        print(f'Test project: {project}', flush=True)
        try:
            config = json.loads(compose('config', '--format', 'json').stdout)
            services = config['services']
            check(set(services) == {'db', 'feedback', 'dashboard'}, 'Expected exactly three services')
            check(not services['db'].get('ports'), 'Database must not publish a host port')
            for name, port in [('feedback', 6110), ('dashboard', 6111)]:
                check(services[name]['environment']['DB_HOST'] == 'db', 'Use Compose DNS')
                check(services[name]['environment']['DB_PORT'] == '5432', 'Use internal DB port')
                check([int(p['published']) for p in services[name]['ports']] == [port],
                      'Wrong application port')
            compose('up', '--build', '-d', '--wait', '--wait-timeout', '120', capture=False)
            for attempt in range(30):
                try:
                    check(http(6110)[0] == 200, 'Feedback form must load')
                    break
                except (URLError, ConnectionError):
                    if attempt == 29:
                        raise
                    time.sleep(1)
            check(count() == 0, 'Fresh database must be empty')
            summary(0, 'No data yet', [0, 0, 0, 0])
            print('PASS: three services, ports, internal networking, empty database', flush=True)

            samples = [(1, 'Docker'), (3, 'Docker'), (5, 'Kubernetes')]
            for difficulty, topic in samples:
                status, body, _ = http(6110, {'difficulty': difficulty, 'topic': topic})
                check(status == 200 and SUCCESS in body, 'Successful submission must be visible')
            check(count() == 3, 'Each valid submission must create one row')
            summary(3, '3.00', [0, 2, 1, 0])
            check(http(6110)[0] == 200 and count() == 3, 'GET must not duplicate feedback')
            for topic in ('Virtual Machine', 'Serverless'):
                check(http(6110, {'difficulty': 3, 'topic': topic})[0] == 200, 'All topics must work')
            summary(5, '3.00', [1, 2, 1, 1])
            print('PASS: form submissions, all topics, exact sample statistics, refresh', flush=True)

            invalid = [{'difficulty': value, 'topic': 'Docker'}
                       for value in ('', '0', '6', '-1', '2.5', 'abc')]
            invalid += [{'difficulty': '3', 'topic': value}
                        for value in ('', 'docker', "Docker'); DROP TABLE feedback; --")]
            invalid += [{}, {'difficulty': '3'}, {'topic': 'Docker'}]
            for data in invalid:
                status, body, _ = http(6110, data)
                check(status == 400 and SUCCESS not in body, 'Invalid input must be rejected')
            check(count() == 5, 'Invalid input must not write records')
            for values in ("(0, 'Docker')", "(6, 'Docker')", "(3, 'Invalid')",
                           "(NULL, 'Docker')", "(3, NULL)"):
                check(sql('INSERT INTO public.feedback(difficulty,topic) VALUES ' + values + ';',
                          required=False).returncode != 0, 'Database constraint missing')
            check(count() == 5, 'Database constraint failure must not insert')
            check(http(6111, {})[0] == 405, 'Dashboard must be read-only')
            readonly = '''from dashboard.db import connect
import psycopg
try:
    with connect() as connection:
        connection.execute("DELETE FROM public.feedback")
except psycopg.errors.ReadOnlySqlTransaction:
    print("Read-only transaction enforced")
else:
    raise AssertionError("Dashboard connection permitted writes")
'''
            compose('exec', '-T', 'dashboard', 'python', '-', stdin=readonly)
            logs = compose('logs', '--no-color', 'feedback').stdout
            check(logs.count(SUCCESS + ':') == 5, 'Exactly one success log per valid write')
            for difficulty, topic in samples:
                check(f'difficulty={difficulty}, topic={topic}' in logs, 'Missing submission details')
            print('PASS: 12 invalid submissions, database constraints, read-only access, logs', flush=True)

            compose('stop', 'db')
            status, body, _ = http(6110, {'difficulty': 2, 'topic': 'Docker'})
            check(status == 503 and SUCCESS not in body, 'Database failure must not report success')
            status, body, _ = http(6111)
            check(status == 503 and 'id="total"' not in body, 'Database failure must not show zero totals')
            logs = compose('logs', '--no-color', 'feedback').stdout
            check(logs.count(SUCCESS + ':') == 5, 'Failed writes must not log success')
            compose('up', '-d', '--wait', '--wait-timeout', '120')
            check(count() == 5, 'Failed write must not create a record')
            summary(5, '3.00', [1, 2, 1, 1])
            check(http(6110, {'difficulty': 4, 'topic': 'Docker'})[0] == 200,
                  'Feedback writes must recover after database restart')
            summary(6, '3.17', [1, 3, 1, 1])
            print('PASS: database outage, no false success, automatic recovery', flush=True)

            compose('down')
            compose('up', '-d', '--wait', '--wait-timeout', '120')
            check(count() == 6, 'Records must survive container recreation')
            summary(6, '3.17', [1, 3, 1, 1])
            compose('exec', '-T', 'dashboard', 'python', '-m', 'unittest',
                    'discover', '-s', 'dashboard/tests', '-v', capture=False)
            check(count() == 6, 'Dashboard tests must leave application data unchanged')
            print('PASS: persistent volume and four existing dashboard tests', flush=True)
            print('All full-stack checks passed.', flush=True)
        finally:
            # This UUID project and its volume were created solely by this test.
            compose('down', '--volumes', capture=False)


if __name__ == '__main__':
    main()
