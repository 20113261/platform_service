if __name__ == '__main__':
    from mioji.common.logger import logger
    import logging
    import requests
    
    logger.basicConfig(level=logging.DEBUG)
    s = requests.Session()
    s.get('http://httpbin.org/cookies/set/sessioncookie/12345678s9')
    s.get('http://httpbin.org/cookies/set/anothercookie/12345678s9')
    r = s.get("http://httpbin.org/cookies")
    print(r.text)