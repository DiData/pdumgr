from requests import post as reqpost, get as reqget, put as reqput

class D42:
    __lastResponse = None
    __user = None
    __pass = None
    __baseUrl = None

    def __init__(self, baseUrl, d42user, d42pass):
        self.__user = d42user
        self.__pass = d42pass
        self.__baseUrl = baseUrl

    def api_post(self, url, params):
        r = reqpost(
            '%s%s' % (self.__baseUrl, url),
            auth=(self.__user, self.__pass),
            data=params
        )
        try:
            return r.json()
        except ValueError:
            print 'Bad JSON data?', r.text

    def api_get(self, url):
        r = reqget(
            '%s%s' % (self.__baseUrl, url),
            auth=(self.__user, self.__pass)
        )
        try:
            return r.json()
        except ValueError:
            print 'Bad JSON data?', r.text

    def api_put(self, url, params):
        r = reqput(
            '%s%s' % (self.__baseUrl, url),
            auth=(self.__user, self.__pass),
            data=params
        )
        try:
            return r.json()
        except ValueError:
            print 'Bad JSON data?', r.text
