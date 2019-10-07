from aiohttp import web
import aiohttp_cors

from routes import routes

routes.static('/spec','../client/build')

app = web.Application()
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})

app.add_routes(routes)

for route in list(app.router.routes()):
    cors.add(route)

web.run_app(app,port=8088)