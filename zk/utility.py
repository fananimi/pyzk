class Utility(object):
    """Utility Class"""

    def __init__(self):
        pass

    @staticmethod
    def filter_by_date(attendances_list, start=None, end=None):
        """
        Select only desire attendances records by datetime condition.

        :param attendances_list: The list of attendances records.
        :param start: The filter of starting datetime
        :param end: The filter of ending datetime
        :return: Limited list of attendances records.
        """
        filtered = []

        if start is not None:
            for d in attendances_list:
                if d.timestamp >= start:
                    filtered.append(d)

        if end is not None:
            for d in attendances_list:
                if d.timestamp <= end:
                    filtered.append(d)

        return filtered

    @staticmethod
    def filter_by_user(attendances_list, users_list):
        """
        Select only desire attendances records by user condition.

        :param attendances_list: The list of attendances records.
        :param users_list: The list of desire users to be select.
        :return: Limited list of attendances records.
        """
        return [
            item
            for item in attendances_list
            if item.user_id in list(map(str, users_list))
        ]
