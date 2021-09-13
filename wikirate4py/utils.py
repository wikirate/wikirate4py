from pandas import DataFrame

from wikirate4py.mixins import WikiRateEntity


def to_dataframe(data):
    if not isinstance(data, list):
        if isinstance(data, WikiRateEntity):
            array = [data.json()]
            return DataFrame.from_dict(array)
        else:
            raise BaseException("""Invalid Input! Provide as input a WikiRateEntity or a list of 
                                            WikiRateEntity objects!""")
    else:
        array = []
        for snippet in data:
            if isinstance(snippet, WikiRateEntity):
                array.append(snippet.json())
            else:
                raise BaseException("""Invalid Input! Provide as input a WikiRateEntity or a list of 
                                                WikiRateEntity objects!""")
        return DataFrame.from_dict(array)