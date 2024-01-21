
def device_type(data):
    """
    Get device_type from the dictionnary, Generic by default

    :param Device device: device to analyse

    :returns: None
    """

    if data[0].get("hardware") is not None :
        if isinstance(data[0].get("hardware"), list):
            data[0]["hardware"] = data[0].get("hardware")[0]
    return data


