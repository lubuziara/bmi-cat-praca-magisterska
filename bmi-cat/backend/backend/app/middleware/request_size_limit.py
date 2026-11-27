from starlette.responses import JSONResponse


class RequestSizeLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] not in ('POST', 'PUT', 'PATCH'):
            return await self.app(scope, receive, send)
        limit = 12 * 1024 * 1024 if scope['path'] == '/api/auth/documents' else 65536
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body = message.get('body', b'')
            size += len(body)
            if size > limit:
                return await JSONResponse({'detail': 'Przesyłane dane są zbyt duże.'}, status_code=413)(scope, receive, send)
            chunks.append(body)
            if not message.get('more_body', False):
                break
        consumed = False

        async def limited_receive():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}

        await self.app(scope, limited_receive, send)
