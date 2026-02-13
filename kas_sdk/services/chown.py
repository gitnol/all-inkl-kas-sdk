from .base import BaseService


class ChownService(BaseService):
    """
    Handles Chown (Owner Reset) operations.
    """

    _YES_NO = ("Y", "N")

    def update_chown(self, chown_path: str, chown_user: str, recursive: str = "N") -> bool:
        """
        Bearbeiten der Besitzrechte.

        Raises:
            ValueError: Bei ungültigem recursive-Wert.
        """
        if recursive not in self._YES_NO:
            raise ValueError(
                f"recursive must be one of {self._YES_NO}, got '{recursive}'"
            )

        params = {
            'chown_path': chown_path,
            'chown_user': chown_user,
            'recursive': recursive
        }
        res = self.client.request('update_chown', params)
        return res.get('ReturnString') == 'TRUE'
