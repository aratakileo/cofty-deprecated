class MethodFinishedError(BaseException):
    def __init__(self):
        super(MethodFinishedError, self).__init__("This method is not finished!")


def isnotfinished():
    raise MethodFinishedError()
