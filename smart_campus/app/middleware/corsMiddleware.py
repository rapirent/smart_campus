class corsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path_info == '/users/get_user_web_screenshot/':
            response["Access-Control-Allow-Origin"] = "*"

        return response