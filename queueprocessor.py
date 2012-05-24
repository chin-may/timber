def processdata(processQueue):
    while True:
        data,fd = processQueue.get()
        print data + ' from ' + str(fd)

