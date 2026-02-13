from .base import BaseService
from typing import Dict, Any, List


class MailingListService(BaseService):
    """
    Handles MailingList operations.
    """

    _YES_NO = ("Y", "N")

    def get_mailinglists(self, mailinglist_name: str = None) -> List[Dict[str, Any]]:
        """
        Auslesen der Mailinglisten
        """
        params = {}
        if mailinglist_name:
            params['mailinglist_name'] = mailinglist_name

        res = self.client.request('get_mailinglists', params)
        if res and 'ReturnInfo' in res:
            return res['ReturnInfo']
        return []

    def add_mailinglist(
        self,
        mailinglist_name: str,
        mailinglist_domain: str,
        mailinglist_password: str,
    ) -> str:
        """
        Anlegen einer Mailingliste
        """
        params = {
            'mailinglist_name': mailinglist_name,
            'mailinglist_domain': mailinglist_domain,
            'mailinglist_password': mailinglist_password,
        }
        res = self.client.request('add_mailinglist', params)
        return res.get('ReturnInfo', 'TRUE')

    def delete_mailinglist(self, mailinglist_name: str) -> bool:
        """
        Löschen einer Mailingliste
        """
        params = {'mailinglist_name': mailinglist_name}
        res = self.client.request('delete_mailinglist', params)
        return res.get('ReturnString') == 'TRUE'

    def update_mailinglist(
        self,
        mailinglist_name: str,
        config: str,
        subscriber: str = None,
        restrict_post: str = None,
        is_active: str = None,
    ) -> bool:
        """
        Bearbeiten der Mailingliste.

        Raises:
            ValueError: Bei ungültigem is_active-Wert.
        """
        if is_active is not None and is_active not in self._YES_NO:
            raise ValueError(
                f"is_active must be one of {self._YES_NO}, got '{is_active}'"
            )

        params = {
            'mailinglist_name': mailinglist_name,
            'config': config,
        }
        if subscriber is not None:
            params['subscriber'] = subscriber
        if restrict_post is not None:
            params['restrict_post'] = restrict_post
        if is_active is not None:
            params['is_active'] = is_active

        res = self.client.request('update_mailinglist', params)
        return res.get('ReturnString') == 'TRUE'
