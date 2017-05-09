if __name__ == '__main__':
    from proj.tasks import vote

    for i in range(3000):
        vote.delay()
