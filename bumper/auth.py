# class ConfServer_AuthHandler:
#     def __init__(self):
#         self.get_milli_time = bumper.ConfServer.get_milli_time
#         pass
#
#     def generate_token(self, user):
#         try:
#             tmpaccesstoken = uuid.uuid4().hex
#             bumper.user_add_token(user["userid"], tmpaccesstoken)
#             return tmpaccesstoken
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     def generate_authcode(self, user, countrycode, token):
#         try:
#             tmpauthcode = "{}_{}".format(countrycode, uuid.uuid4().hex)
#             bumper.user_add_authcode(user["userid"], token, tmpauthcode)
#             return tmpauthcode
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     async def login(self, request):
#         try:
#             user_devid = request.match_info.get("devid", "")
#             countrycode = request.match_info.get("country", "us")
#             apptype = request.match_info.get("apptype", "")
#             webserver_log.info(
#                 "client with devid {} attempting login".format(user_devid)
#             )
#             if bumper.use_auth:
#                 if (
#                         not user_devid == ""
#                 ):  # Performing basic "auth.py" using devid, super insecure
#                     user = bumper.user_by_deviceid(user_devid)
#                     if "checkLogin" in request.path:
#                         self.check_token(
#                             apptype, countrycode, user, request.query["accessToken"]
#                         )
#                     else:
#                         if "global_" in apptype:  # EcoVacs Home
#                             login_details = EcoVacsHome_Login()
#                             login_details.ucUid = "fuid_{}".format(user["userid"])
#                             login_details.loginName = "fusername_{}".format(
#                                 user["userid"]
#                             )
#                             login_details.mobile = None
#
#                         else:
#                             login_details = EcoVacs_Login()
#
#                         # Deactivate old tokens and authcodes
#                         bumper.user_revoke_expired_tokens(user["userid"])
#
#                         login_details.accessToken = self.generate_token(user)
#                         login_details.uid = "fuid_{}".format(user["userid"])
#                         login_details.username = "fusername_{}".format(user["userid"])
#                         login_details.country = countrycode
#                         login_details.email = "null@null.com"
#
#                         body = {
#                             "code": API_ERRORS[RETURN_API_SUCCESS],
#                             "data": json.loads(login_details.toJSON()),
#                             # {
#                             #    "accessToken": self.generate_token(tmpuser),  # Generate a token
#                             #    "country": countrycode,
#                             #    "email": "null@null.com",
#                             #    "uid": "fuid_{}".format(tmpuser["userid"]),
#                             #    "username": "fusername_{}".format(tmpuser["userid"]),
#                             # },
#                             "msg": "操作成功",
#                             "time": self.get_milli_time(datetime.utcnow().timestamp()),
#                         }
#
#                         return web.json_response(body)
#
#                 body = {
#                     "code": bumper.ERR_USER_NOT_ACTIVATED,
#                     "data": None,
#                     "msg": "当前密码错误",
#                     "time": self.get_milli_time(datetime.utcnow().timestamp()),
#                 }
#
#                 return web.json_response(body)
#
#             else:
#                 return web.json_response(
#                     self._auth_any(user_devid, apptype, countrycode, request)
#                 )
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     async def get_AuthCode(self, request):
#         try:
#             apptype = request.match_info.get("apptype", "")
#             user_devid = request.match_info.get("devid", "")  # Ecovacs
#             if user_devid == "":
#                 user_devid = request.query["deviceId"]  # Ecovacs Home
#
#             if not user_devid == "":
#                 user = bumper.user_by_deviceid(user_devid)
#                 token = ""
#                 if user:
#                     if "accessToken" in request.query:
#                         token = bumper.user_get_token(
#                             user["userid"], request.query["accessToken"]
#                         )
#                     if token:
#                         authcode = ""
#                         if not "authcode" in token:
#                             authcode = self.generate_authcode(
#                                 user,
#                                 request.match_info.get("country", "us"),
#                                 request.query["accessToken"],
#                             )
#                         else:
#                             authcode = token["authcode"]
#                         if "global" in apptype:
#                             body = {
#                                 "code": bumper.RETURN_API_SUCCESS,
#                                 "data": {
#                                     "authCode": authcode,
#                                     "ecovacsUid": request.query["uid"],
#                                 },
#                                 "msg": "操作成功",
#                                 "success": True,
#                                 "time": self.get_milli_time(
#                                     datetime.utcnow().timestamp()
#                                 ),
#                             }
#                         else:
#                             body = {
#                                 "code": bumper.RETURN_API_SUCCESS,
#                                 "data": {
#                                     "authCode": authcode,
#                                     "ecovacsUid": request.query["uid"],
#                                 },
#                                 "msg": "操作成功",
#                                 "time": self.get_milli_time(
#                                     datetime.utcnow().timestamp()
#                                 ),
#                             }
#                         return web.json_response(body)
#
#             body = {
#                 "code": bumper.ERR_TOKEN_INVALID,
#                 "data": None,
#                 "msg": "当前密码错误",
#                 "time": self.get_milli_time(datetime.utcnow().timestamp()),
#             }
#
#             return web.json_response(body)
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     def check_token(self, apptype, countrycode, user, token):
#         try:
#             if bumper.check_token(user["userid"], token):
#
#                 if "global_" in apptype:  # EcoVacs Home
#                     login_details = EcoVacsHome_Login()
#                     login_details.ucUid = "fuid_{}".format(user["userid"])
#                     login_details.loginName = "fusername_{}".format(user["userid"])
#                     login_details.mobile = None
#                 else:
#                     login_details = EcoVacs_Login()
#
#                 login_details.accessToken = token
#                 login_details.uid = "fuid_{}".format(user["userid"])
#                 login_details.username = "fusername_{}".format(user["userid"])
#                 login_details.country = countrycode
#                 login_details.email = "null@null.com"
#
#                 body = {
#                     "code": bumper.RETURN_API_SUCCESS,
#                     "data": json.loads(login_details.toJSON()),
#                     # {
#                     #    "accessToken": self.generate_token(tmpuser),  # Generate a token
#                     #    "country": countrycode,
#                     #    "email": "null@null.com",
#                     #    "uid": "fuid_{}".format(tmpuser["userid"]),
#                     #    "username": "fusername_{}".format(tmpuser["userid"]),
#                     # },
#                     "msg": "操作成功",
#                     "time": self.get_milli_time(datetime.utcnow().timestamp()),
#                 }
#                 return web.json_response(body)
#
#             else:
#                 body = {
#                     "code": bumper.ERR_TOKEN_INVALID,
#                     "data": None,
#                     "msg": "当前密码错误",
#                     "time": self.get_milli_time(datetime.utcnow().timestamp()),
#                 }
#                 return web.json_response(body)
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     def _auth_any(self, devid, apptype, country, request):
#         try:
#             user_devid = devid
#             countrycode = country
#             user = bumper.user_by_deviceid(user_devid)
#             bots = bumper.db_get().table("bots").all()
#
#             if user:  # Default to user 0
#                 tmpuser = user
#                 if "global_" in apptype:  # EcoVacs Home
#                     login_details = EcoVacsHome_Login()
#                     login_details.ucUid = "fuid_{}".format(tmpuser["userid"])
#                     login_details.loginName = "fusername_{}".format(tmpuser["userid"])
#                     login_details.mobile = None
#                 else:
#                     login_details = EcoVacs_Login()
#
#                 login_details.accessToken = self.generate_token(tmpuser)
#                 login_details.uid = "fuid_{}".format(tmpuser["userid"])
#                 login_details.username = "fusername_{}".format(tmpuser["userid"])
#                 login_details.country = countrycode
#                 login_details.email = "null@null.com"
#                 bumper.user_add_device(tmpuser["userid"], user_devid)
#             else:
#                 bumper.user_add("tmpuser")  # Add a new user
#                 tmpuser = bumper.user_get("tmpuser")
#                 if "global_" in apptype:  # EcoVacs Home
#                     login_details = EcoVacsHome_Login()
#                     login_details.ucUid = "fuid_{}".format(tmpuser["userid"])
#                     login_details.loginName = "fusername_{}".format(tmpuser["userid"])
#                     login_details.mobile = None
#                 else:
#                     login_details = EcoVacs_Login()
#
#                 login_details.accessToken = self.generate_token(tmpuser)
#                 login_details.uid = "fuid_{}".format(tmpuser["userid"])
#                 login_details.username = "fusername_{}".format(tmpuser["userid"])
#                 login_details.country = countrycode
#                 login_details.email = "null@null.com"
#                 bumper.user_add_device(tmpuser["userid"], user_devid)
#
#             for bot in bots:  # Add all bots to the user
#                 if "did" in bot:
#                     bumper.user_add_bot(tmpuser["userid"], bot["did"])
#                 else:
#                     webserver_log.error("No DID for bot: {}".format(bot))
#
#             if "checkLogin" in request.path:  # If request was to check a token do so
#                 checkToken = self.check_token(
#                     apptype, countrycode, tmpuser, request.query["accessToken"]
#                 )
#                 isGood = json.loads(checkToken.text)
#                 if isGood["code"] == "0000":
#                     return isGood
#
#             # Deactivate old tokens and authcodes
#             bumper.user_revoke_expired_tokens(tmpuser["userid"])
#
#             body = {
#                 "code": bumper.RETURN_API_SUCCESS,
#                 "data": json.loads(login_details.toJSON()),
#                 # {
#                 #    "accessToken": self.generate_token(tmpuser),  # Generate a token
#                 #    "country": countrycode,
#                 #    "email": "null@null.com",
#                 #    "uid": "fuid_{}".format(tmpuser["userid"]),
#                 #    "username": "fusername_{}".format(tmpuser["userid"]),
#                 # },
#                 "msg": "操作成功",
#                 "time": self.get_milli_time(datetime.utcnow().timestamp()),
#             }
#
#             return body
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     def getUserAccountInfo(self, request):
#         try:
#             user_devid = request.match_info.get("devid", "")
#             countrycode = request.match_info.get("country", "us")
#             apptype = request.match_info.get("apptype", "")
#             user = bumper.user_by_deviceid(user_devid)
#
#             if "global_" in apptype:  # EcoVacs Home
#                 login_details = EcoVacsHome_Login()
#                 login_details.ucUid = "fuid_{}".format(user["userid"])
#                 login_details.loginName = "fusername_{}".format(user["userid"])
#                 login_details.mobile = None
#             else:
#                 login_details = EcoVacs_Login()
#
#             login_details.uid = "fuid_{}".format(user["userid"])
#             login_details.username = "fusername_{}".format(user["userid"])
#             login_details.country = countrycode
#             login_details.email = "null@null.com"
#
#             body = {
#                 "code": bumper.RETURN_API_SUCCESS,
#                 "data": {
#                     "email": login_details.email,
#                     "hasMobile": "N",
#                     "hasPassword": "Y",
#                     "uid": login_details.uid,
#                     "userName": login_details.username,
#                     "obfuscatedMobile": None,
#                     "mobile": None,
#                     "loginName": login_details.loginName,
#                 },
#                 "msg": "操作成功",
#                 "time": self.get_milli_time(datetime.utcnow().timestamp()),
#             }
#
#             # Example body
#             # {
#             # "code": "0000",
#             # "data": {
#             #     "email": "user@gmail.com",
#             #     "hasMobile": "N",
#             #     "hasPassword": "Y",
#             #     "headIco": "",
#             #     "loginName": "user@gmail.com",
#             #     "mobile": null,
#             #     "mobileAreaNo": null,
#             #     "nickname": "",
#             #     "obfuscatedMobile": null,
#             #     "thirdLoginInfoList": [
#             #     {
#             #         "accountType": "WeChat",
#             #         "hasBind": "N"
#             #     }
#             #     ],
#             #     "uid": "20180719212155_*****",
#             #     "userName": "EAY*****"
#             # },
#             # "msg": "操作成功",
#             # "success": true,
#             # "time": 1578203898343
#             # }
#
#             return web.json_response(body)
#
#         except Exception as e:
#             webserver_log.exception("{}".format(e))
#
#     async def logout(self, request):
#         user_devid = request.match_info.get("devid", "")
#         if not user_devid == "":
#             user = bumper.user_by_deviceid(user_devid)
#             if user:
#                 if bumper.check_token(user["userid"], request.query["accessToken"]):
#                     # Deactivate old tokens and authcodes
#                     bumper.user_revoke_token(
#                         user["userid"], request.query["accessToken"]
#                     )
#
#         body = {
#             "code": bumper.RETURN_API_SUCCESS,
#             "data": None,
#             "msg": "操作成功",
#             "time": self.get_milli_time(datetime.utcnow().timestamp()),
#         }
#
#         return web.json_response(body)