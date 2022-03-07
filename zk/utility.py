class Utility(object):
    """Utility Class"""

    def __init__(self):
        pass

    @staticmethod
    def filter_by_date():
        ...

    @staticmethod
    def filter_by_user(attendances_list, users_list):
        """

        :param attendances_list:
        :param users_list:
        :return:
        """

        return [
            item
            for item in attendances_list
            if item.user_id in list(map(str, users_list))
        ]
