def with_logger(logger):
    def _with_logger(cls):
        class NewClass(cls):
            def __init__(self, *args, **kwargs):
                self.logger = logger.getChild(cls.__class__.__name__)
                super(NewClass, self).__init__(*args, **kwargs)
    return _with_logger
