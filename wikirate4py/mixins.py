class WikirateEntity(object):
    __slots__ = ()

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    def json(self):
        return {key: getattr(self, key, None) for key in self.__slots__ if key != "raw"}

    def raw_json(self):
        return self.raw

    def get_parameters(self):
        return self.__slots__

    def __repr__(self):
        return str(self.json())
