from proj.celery import app

@app.task(bind=True)
def abc(self):
    print 'Hello World'

abc()