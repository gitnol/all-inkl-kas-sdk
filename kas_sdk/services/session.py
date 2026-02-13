from .base import BaseService
from typing import Dict, Any


class SessionService(BaseService):
    """
    Handles Session operations (KAS SSO).
    """

    _YES_NO = ("Y", "N")

    def add_session(
        self,
        session_lifetime: int = 1800,
        session_update_lifetime: str = "N",
        session_2fa: str = None,
    ) -> str:
        """
        Create a new KAS session token.

        Args:
            session_lifetime (int): Seconds valid.
            session_update_lifetime (str): 'Y'/'N' - update on activity?
            session_2fa (str): OTP pin if 2-factor auth is active (optional).

        Returns:
            str: The Session ID (KasSessionId) to be used in URLs.

        Raises:
            ValueError: Bei ungültigem session_update_lifetime-Wert.
        """
        if session_update_lifetime not in self._YES_NO:
            raise ValueError(
                f"session_update_lifetime must be one of {self._YES_NO}, got '{session_update_lifetime}'"
            )

        params = {
            'session_lifetime': session_lifetime,
            'session_update_lifetime': session_update_lifetime,
        }
        if session_2fa:
            params['session_2fa'] = session_2fa
        res = self.client.request('add_session', params)
        return res.get('ReturnInfo', 'TRUE')
