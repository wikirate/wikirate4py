class Cursor(object):

    def __init__(self, method, per_page=20, offset=0, **kwargs):
        self.method = method
        self.kwargs = kwargs
        if per_page > 200:
            self.per_page = 200
        else:
            self.per_page = per_page

        self.offset = offset
        self.limit = per_page
        self.items = None

    def has_next(self) -> bool:
        self.items = self.method(offset=self.offset, limit=self.limit, **self.kwargs)
        return len(self.items) > 0

    def next(self):
        self.offset += self.per_page
        return self.items
