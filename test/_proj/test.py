import time


def add(a, b):
    return a + b

for i in range(100):
    r = add(i,2)
    print(r)
    time.sleep(0.2)