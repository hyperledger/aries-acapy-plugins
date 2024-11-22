"""DID Manager Base Classes."""

from abc import ABC, abstractmethod

from acapy_agent.core.profile import Profile
from acapy_agent.wallet.base import BaseWallet
from acapy_agent.wallet.util import b64_to_bytes, bytes_to_b64
from aiohttp import web


class BaseDIDRegistrar(ABC):
    """Base class for DID Registrars."""

    @abstractmethod
    async def create(self, options: dict = None) -> dict:
        """Create a new DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update(self, options: dict = None) -> dict:
        """Update an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def deactivate(self, options: dict = None) -> dict:
        """Deactivate an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def create_resource(self, did: str, options: dict) -> dict:
        """Create a DID Linked Resource."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update_resource(self, did: str, options: dict) -> dict:
        """Update a DID Linked Resource."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def deactivate_resource(self, did: str, options: dict) -> dict:
        """Deactivate a DID Linked Resource."""
        raise NotImplementedError("Subclasses must implement this method")


class BaseDIDManager(ABC):
    """Base class for DID Managers."""

    def __init__(self, profile: Profile) -> None:
        """Initialize the DID Manager."""
        self.profile = profile

    @abstractmethod
    async def create(self, did_doc: dict, options: dict = None) -> web.Response:
        """Create a new DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update(self, did: str, did_doc: dict, options: dict = None) -> web.Response:
        """Update an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def deactivate(self, did: str, options: dict = None) -> web.Response:
        """Deactivate an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    async def sign_requests(
        self, wallet: BaseWallet, signing_requests: list, verkey: str = None
    ) -> list:
        """Sign all requests in the signing_requests list.

        Args:
            wallet: Wallet instance used to sign messages.
            signing_requests: List of signing request dictionaries.
            verkey (optional): Pre-determined verkey to use for signing. \
                If None, retrieve verkey from the wallet.

        Returns:
            List of signed responses, each containing 'kid' and 'signature'.
        """
        signed_responses = []
        for sign_req in signing_requests:
            kid = sign_req.get("kid")
            payload_to_sign = sign_req.get("serializedPayload")
            if verkey:
                # Assign verkey to key ID in wallet
                await wallet.assign_kid_to_key(verkey, kid)
            else:
                # Retrive verkey from wallet
                key = await wallet.get_key_by_kid(kid)
                if not key:
                    raise ValueError(f"No key found for kid: {kid}")
                verkey = key.verkey
            # sign payload
            signature_bytes = await wallet.sign_message(
                b64_to_bytes(payload_to_sign), verkey
            )

            signed_responses.append(
                {
                    "kid": kid,
                    "signature": bytes_to_b64(signature_bytes),
                }
            )

        return signed_responses

    async def validate_did_doc(self, did_doc: dict) -> bool:
        """Validate the structure of the DID Document."""
        if not did_doc.get("id"):
            raise web.HTTPBadRequest(reason="DID Document must have an 'id'")
        # TODO Additional validation logic
        return True

    def format_response(
        self, success: bool, result: dict = None, error: str = None
    ) -> dict:
        """Format the response for operations."""
        return {
            "success": success,
            "result": result if success else None,
            "error": error if not success else None,
        }
