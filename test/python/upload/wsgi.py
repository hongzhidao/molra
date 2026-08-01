from email.parser import BytesFeedParser
from email.policy import default
from tempfile import TemporaryFile


def read(environ):
    length = int(environ.get('CONTENT_LENGTH', 0))

    body = TemporaryFile(mode='w+b')
    body.write(bytes(environ['wsgi.input'].read(length)))
    body.seek(0)

    environ['wsgi.input'] = body
    return body


def application(environ, start_response):
    file = read(environ)

    parser = BytesFeedParser(policy=default)
    headers = 'Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n'
    parser.feed((headers % environ['CONTENT_TYPE']).encode())

    while True:
        chunk = file.read(8192)

        if not chunk:
            break

        parser.feed(chunk)

    message = parser.close()
    part = next(item for item in message.walk() if item.get_filename())

    filename = part.get_filename()
    data = filename.encode() + part.get_payload(decode=True)

    start_response(
        '200 OK',
        [('Content-Type', 'text/plain'), ('Content-Length', str(len(data)))],
    )

    return data
