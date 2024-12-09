from pandas import DataFrame

from wikirate4py.mixins import WikirateEntity


def to_dataframe(data):
    if not isinstance(data, list):
        if isinstance(data, WikirateEntity):
            array = [data.json()]
            return DataFrame.from_dict(array)
        else:
            raise BaseException("""Invalid Input! Provide as input a WikirateEntity or a list of 
                                            WikirateEntity objects!""")
    else:
        array = []
        for snippet in data:
            if isinstance(snippet, WikirateEntity):
                array.append(snippet.json())
            else:
                raise BaseException("""Invalid Input! Provide as input a WikiRateEntity or a list of 
                                                WikirateEntity objects!""")
        return DataFrame.from_dict(array)