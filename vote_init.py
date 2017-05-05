if __name__ == '__main__':
    from proj.tasks import vote

    for i in range(1000):
        vote.delay()
