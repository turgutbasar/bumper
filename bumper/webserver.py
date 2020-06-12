#!/usr/bin/env python3

import asyncio
import logging
import os

import jinja2
from aiohttp import web
from aiohttp_jinja2 import *

import bumper
from bumper import plugins
from bumper.models import *


class AccessLogFilter(logging.Filter):
    def filter(self, record):
        if (
            record.levelno == 10
            and logging.getLogger("confserver").getEffectiveLevel() == 10
        ):
            return True
        else:
            return False


webserver_log = logging.getLogger("confserver")
logging.getLogger("aiohttp.access").addFilter(AccessLogFilter())  # Add filter to aiohttp.access


class WebServer:
    def __init__(self, address):
        self.address = address
        self.app = None
        self.site = None
        self.runner = None
        self.runners = []
        self.excludelogging = ["base", "remove-bot", "remove-client", "restart-service"]

    @staticmethod
    def get_milli_time(timetoconvert):
        return int(round(timetoconvert * 1000))

    def load(self):
        self.app = web.Application(loop=asyncio.get_event_loop(), middlewares=[
            self.log_all_requests,
            ])

        loader = jinja2.FileSystemLoader(os.path.join(bumper.bumper_dir, "bumper", "web", "templates"));
        setup(self.app, loader=loader)

        self.app.add_routes(
            [
                web.get("", WebServer.handle_base, name="base"),
                web.get("/bot/remove/{did}", self.handle_RemoveBot, name='remove-bot'),       
                web.get("/client/remove/{resource}", self.handle_RemoveClient, name='remove-client'),      
                web.get("/restart_{service}", self.handle_RestartService, name='restart-service'),                
                web.post("/lookup.do", self.handle_lookup),
            ]
        )

        # Sub Apps
        sub_apps = {
            "/v1/": web.Application(),
            "/v2/": web.Application(),
            "/api/": web.Application(),
            "/upload/": web.Application()
        }

        # Load plugins
        for plug in bumper.discovered_plugins:
            if isinstance(bumper.discovered_plugins[plug].plugin, bumper.plugins.ConfServerApp):                
                plugin = bumper.discovered_plugins[plug].plugin                
                if plugin.plugin_type == "sub_api":  # app or sub_api
                    if plugin.sub_api in sub_apps.keys():
                        if plugin.routes:
                            logging.debug(f"Adding web server sub_api ({plugin.name})")
                            sub_apps.get(plugin.sub_api).add_routes(plugin.routes)
                
                elif plugin.plugin_type == "app":
                    if plugin.path_prefix and plugin.app:
                        logging.debug(f"Adding web server plugin ({plugin.name})")
                        self.app.add_subapp(plugin.path_prefix, plugin.app)      

        # Add sub_apps to app
        for path_prefix in sub_apps.keys():
            self.app.add_subapp(path_prefix, sub_apps[path_prefix])

    async def start(self):
        self.load()
        webserver_log.info(
            "Starting WebServer at {}:{}".format(self.address[0], self.address[1])
        )
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(
            self.runner, host=self.address[0], port=self.address[1]
        )

        await self.site.start()

    async def stop(self):
        await self.runner.shutdown()

    @staticmethod
    async def handle_base(request):
        context = {
            "bots": bumper.db_get().table("bots").all(),
            "clients": bumper.db_get().table("clients").all(),
            "xmpp_server": bumper.xmpp_server
        }

        return render_template('home.jinja2', request, context=context)

    @web.middleware
    async def log_all_requests(self, request, handler):

        if request._match_info.route.name not in self.excludelogging:
            
            try:
                if request.content_length:
                    if request.content_type == "application/x-www-form-urlencoded":
                        postbody = await request.post()

                    elif request.content_type == "application/json":
                        try:
                            postbody = json.loads(await request.text())
                        except Exception as e:
                            webserver_log.error("Request body not json: {} - {}".format(e, e.doc))
                            postbody = e.doc
                    
                    else:
                        postbody = await request.post()
                else:
                    postbody = None

                response = await handler(request)
                if not "application/octet-stream" in response.content_type:
                    logall = {
                        "request": {
                        "route_name": f"{request.match_info.route.name}",
                        "method": f"{request.method}",
                        "path": f"{request.path}",
                        "query_string": f"{request.query_string}",
                        "raw_path": f"{request.raw_path}",
                        "raw_headers": f'{",".join(map("{}".format, request.raw_headers))}',
                        "body": f"{postbody}",
                            },

                        "response": {
                        "response_body": f"{json.loads(response.body)}",
                        "status": f"{response.status}",
                        }
                        }
                else:
                    logall = {
                        "request": {
                        "route_name": f"{request.match_info.route.name}",
                        "method": f"{request.method}",
                        "path": f"{request.path}",
                        "query_string": f"{request.query_string}",
                        "raw_path": f"{request.raw_path}",
                        "raw_headers": f'{",".join(map("{}".format, request.raw_headers))}',
                        "body": f"{postbody}",
                            },

                        "response": {
                        "status": f"{response.status}",
                        }
                        }   

                webserver_log.debug(json.dumps(logall))
                
                return response

            except web.HTTPNotFound as notfound:
                webserver_log.debug("Request path {} not found".format(request.raw_path))
                requestlog = {
                    "request": {
                    "route_name": f"{request.match_info.route.name}",
                    "method": f"{request.method}",
                    "path": f"{request.path}",
                    "query_string": f"{request.query_string}",
                    "raw_path": f"{request.raw_path}",
                    "raw_headers": f'{",".join(map("{}".format, request.raw_headers))}',
                    "body": f"{postbody}",
                        }
                }
                webserver_log.debug(json.dumps(requestlog))
                return notfound

            except Exception as e:
                webserver_log.exception("{}".format(e))
                requestlog = {
                    "request": {
                    "route_name": f"{request.match_info.route.name}",
                    "method": f"{request.method}",
                    "path": f"{request.path}",
                    "query_string": f"{request.query_string}",
                    "raw_path": f"{request.raw_path}",
                    "raw_headers": f'{",".join(map("{}".format, request.raw_headers))}',
                    "body": f"{postbody}",
                        }
                }
                webserver_log.debug(json.dumps(requestlog))
                return e 

        else:
            return await handler(request)

    async def restart_XMPP(self):
        bumper.xmpp_server.stop()
        await bumper.xmpp_server.start()

    async def handle_RestartService(self, request):
        service = request.match_info.get("service", "")
        if service == "XMPPServer":
            await self.restart_XMPP()
            return web.json_response({"status": "complete"})
        else:
            return web.json_response({"status": "invalid service"})

    async def handle_RemoveBot(self, request):
        did = request.match_info.get("did", "")
        bumper.bot_remove(did)
        if bumper.bot_get(did):
            return web.json_response({"status": "failed to remove bot"})
        else:
            return web.json_response({"status": "successfully removed bot"})

    async def handle_RemoveClient(self, request):
        resource = request.match_info.get("resource", "")
        bumper.client_remove(resource)
        if bumper.client_get(resource):
            return web.json_response({"status": "failed to remove client"})
        else:
            return web.json_response({"status": "successfully removed client"})

    async def handle_lookup(self, request):
        try:

            body = {}
            postbody = {}
            if request.content_type == "application/x-www-form-urlencoded":
                postbody = await request.post()

            else:
                postbody = json.loads(await request.text())

            webserver_log.debug(postbody)

            todo = postbody["todo"]
            if todo == "FindBest":
                service = postbody["service"]
                if service == "EcoMsgNew":
                    srvip = bumper.bumper_announce_ip
                    srvport = 5223
                    webserver_log.info(
                        "Announcing EcoMsgNew Server to bot as: {}:{}".format(
                            srvip, srvport
                        )
                    )
                    msgserver = {"ip": srvip, "port": srvport, "result": "ok"}
                    msgserver = json.dumps(msgserver)
                    msgserver = msgserver.replace(
                        " ", ""
                    )  # bot seems to be very picky about having no spaces, only way was with text

                    return web.json_response(text=msgserver)

                elif service == "EcoUpdate":
                    srvip = "47.88.66.164"  # EcoVacs Server
                    srvport = 8005
                    webserver_log.info(
                        "Announcing EcoUpdate Server to bot as: {}:{}".format(
                            srvip, srvport
                        )
                    )
                    body = {"result": "ok", "ip": srvip, "port": srvport}

            return web.json_response(body)

        except Exception as e:
            webserver_log.exception("{}".format(e))

    async def disconnect(self):
        webserver_log.info("shutting down")
        await self.app.shutdown()
