from proj.tasks import get_images

if __name__ == '__main__':
    result = get_images.delay('HelloWorld', 'http://jbcdn2.b0.upaiyun.com/2016/12/9573f12727a59f5954f4075e212d9719.png')
    print 'Hello World'
