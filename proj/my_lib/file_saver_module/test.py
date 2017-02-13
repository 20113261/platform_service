import requests

from FileSaver import FileSaver

if __name__ == '__main__':
    page = requests.get('http://www.163.com')
    page.encoding = 'utf8'
    content = page.text
    fs = FileSaver()
    fs.save('asdfasdfsafd', {}, content=content)
