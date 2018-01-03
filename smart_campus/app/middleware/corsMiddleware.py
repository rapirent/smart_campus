class corsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        allowed_API = [
            '/users/get_user_web_screenshot/',
            '/smart_campus/login/',
            '/smart_campus/logout/',
            '/smart_campus/signup/',
        ]
        if request.path_info in allowed_API:
            response["Access-Control-Allow-Origin"] = "*"

        return response