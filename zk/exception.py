# -*- coding: utf-8 -*-
class ZKError(Exception):
    pass


class ZKErrorResponse(ZKError):
    pass


class ZKNetworkError(ZKError):
    pass
