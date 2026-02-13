from .base import BaseService
from typing import Dict, Any, List, Union


class CronjobService(BaseService):
    """
    Handles Cronjob operations.
    """

    _YES_NO = ("Y", "N")
    _PROTOCOL_VALUES = ("http", "https")

    def get_cronjobs(self, cronjob_id: int = None) -> List[Dict[str, Any]]:
        """
        Auslesen der Cronjobs
        """
        params = {}
        if cronjob_id:
            params['cronjob_id'] = cronjob_id

        res = self.client.request('get_cronjobs', params)
        if res and 'ReturnInfo' in res:
            return res['ReturnInfo']
        return []

    def add_cronjob(
        self,
        protocol: str,
        http_url: str,
        cronjob_comment: str,
        minute: str,
        hour: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
        http_user: str = None,
        http_password: str = None,
        mail_address: str = None,
        mail_condition: str = None,
        mail_subject: str = None,
        is_active: str = "Y",
    ) -> bool:
        """
        Anlegen eines Cronjobs.

        Raises:
            ValueError: Bei ungültigem protocol- oder is_active-Wert.
        """
        if protocol not in self._PROTOCOL_VALUES:
            raise ValueError(
                f"protocol must be one of {self._PROTOCOL_VALUES}, got '{protocol}'"
            )

        if is_active not in self._YES_NO:
            raise ValueError(
                f"is_active must be one of {self._YES_NO}, got '{is_active}'"
            )

        params = {
            'protocol': protocol,
            'http_url': http_url,
            'cronjob_comment': cronjob_comment,
            'minute': minute,
            'hour': hour,
            'day_of_month': day_of_month,
            'month': month,
            'day_of_week': day_of_week,
            'is_active': is_active,
        }

        optional_params = {
            'http_user': http_user,
            'http_password': http_password,
            'mail_address': mail_address,
            'mail_condition': mail_condition,
            'mail_subject': mail_subject,
        }

        for k, v in optional_params.items():
            if v is not None:
                params[k] = v

        res = self.client.request('add_cronjob', params)
        return res.get('ReturnString') == 'TRUE'

    def delete_cronjob(self, cronjob_id: int) -> bool:
        """
        Löschen eines Cronjobs
        """
        params = {'cronjob_id': cronjob_id}
        res = self.client.request('delete_cronjob', params)
        return res.get('ReturnString') == 'TRUE'

    def update_cronjob(
        self,
        cronjob_id: int,
        protocol: str = None,
        http_url: str = None,
        cronjob_comment: str = None,
        minute: str = None,
        hour: str = None,
        day_of_month: str = None,
        month: str = None,
        day_of_week: str = None,
        http_user: str = None,
        http_password: str = None,
        mail_address: str = None,
        mail_condition: str = None,
        mail_subject: str = None,
        is_active: str = None,
    ) -> bool:
        """
        Bearbeiten eines Cronjobs.

        Raises:
            ValueError: Bei ungültigem protocol- oder is_active-Wert.
        """
        if protocol is not None and protocol not in self._PROTOCOL_VALUES:
            raise ValueError(
                f"protocol must be one of {self._PROTOCOL_VALUES}, got '{protocol}'"
            )

        if is_active is not None and is_active not in self._YES_NO:
            raise ValueError(
                f"is_active must be one of {self._YES_NO}, got '{is_active}'"
            )

        params = {'cronjob_id': cronjob_id}

        optional_params = {
            'protocol': protocol,
            'http_url': http_url,
            'cronjob_comment': cronjob_comment,
            'minute': minute,
            'hour': hour,
            'day_of_month': day_of_month,
            'month': month,
            'day_of_week': day_of_week,
            'http_user': http_user,
            'http_password': http_password,
            'mail_address': mail_address,
            'mail_condition': mail_condition,
            'mail_subject': mail_subject,
            'is_active': is_active,
        }

        for k, v in optional_params.items():
            if v is not None:
                params[k] = v

        res = self.client.request('update_cronjob', params)
        return res.get('ReturnString') == 'TRUE'
