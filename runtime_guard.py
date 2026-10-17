"""Bounded requests and fail-closed remote admin access; not tenant isolation."""
import hmac
import ipaddress
import os
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_BODY=18*1024*1024


class RuntimeGuard:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        request=Request(scope);method=scope['method'];path=scope['path']
        sensitive=method not in ('GET','HEAD','OPTIONS') or path.startswith(('/api/steles','/api/uploads/','/api/inferences/','/static/results/')) or path.endswith(('/runs','/inferences','/report'))
        remote_mode=os.getenv('RUBBINGMIND_DEPLOYMENT','local')!='local'
        host=(scope.get('client') or ('',0))[0]
        try:loopback=ipaddress.ip_address(host).is_loopback
        except ValueError:loopback=host in ('testclient','localhost')
        if sensitive and (remote_mode or not loopback):
            token=os.getenv('RUBBINGMIND_ADMIN_TOKEN','')
            supplied=request.headers.get('authorization','').removeprefix('Bearer ')
            if not token or not hmac.compare_digest(supplied,token):
                return await JSONResponse({'detail':'远程私有数据及写接口需要管理员认证；本模式不提供多用户隔离'},status_code=401)(scope,receive,send)
        if method in ('POST','PUT','PATCH'):
            try:size=int(request.headers.get('content-length','0'))
            except ValueError:size=MAX_BODY+1
            if size>MAX_BODY:return await JSONResponse({'detail':'请求超过18 MiB限制'},status_code=413)(scope,receive,send)
            body=bytearray()
            while True:
                message=await receive()
                if message['type']=='http.disconnect':return
                body.extend(message.get('body',b''))
                if len(body)>MAX_BODY:return await JSONResponse({'detail':'请求超过18 MiB限制'},status_code=413)(scope,receive,send)
                if not message.get('more_body',False):break
            sent=False
            async def replay():
                nonlocal sent
                if not sent:
                    sent=True;return {'type':'http.request','body':bytes(body),'more_body':False}
                return await receive()
            return await self.app(scope,replay,send)
        return await self.app(scope,receive,send)
