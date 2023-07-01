class LimitedDict(dict):
    def __init__(self, limit: int = 10, *args, **kwargs):
        self.limit = limit
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if len(self) >= self.limit:
            self.pop(next(iter(self)))
        super().__setitem__(key, value)
