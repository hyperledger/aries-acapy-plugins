"""DID Manager Base Classes."""

from abc import ABC, abstractmethod

from acapy_agent.core.profile import Profile
from acapy_agent.core.error import BaseError
from acapy_agent.wallet.base import BaseWallet
from acapy_agent.wallet.util import b64_to_bytes, bytes_to_b64
from aiohttp import web
from pydantic import BaseModel, Field
from typing import Optional, List

from ..routes import DIDDocumentSchema

class SigningResponse(BaseModel):
    """Signing Response."""
    kid: str
    signature: str

# Secret Schema
class Secret(BaseModel):
    """Secret."""
    signingResponse: List[SigningResponse]  # List of SigningResponse objects

# Options Schema
class Options(BaseModel):
    """Options."""
    network: str

# BaseRequestSchema
class SubmitSignatureOptions(BaseModel):
    """Base Request."""
    jobId: str = Field(None, description="This input field is used to keep track of an ongoing operation process", example="4c0cf49a-1839-4900-b870-f63f386d0d43")
    options: Optional[Options] = None
    secret: Secret

# DIDCreateRequestOptions Schema
class DidCreateRequestOptions(BaseModel):
    """DID Create Request Schema."""
    didDocument: Optional[DIDDocumentSchema] = None

# DIDUpdateRequestOptions Schema
class DidUpdateRequestOptions(BaseModel):
    """DID Update Request Schema."""
    did: str
    didDocument: DIDDocumentSchema

# DIDDeactivateRequestOptions Schema
class DidDeactivateRequestOptions(BaseModel):
    """DID Deactivate Request Schema."""
    did: str = Field(None, description="This input field indicates the DID that is the target of the DID deactivation operation.")

# ResourceCreateRequestOptions Schema
class ResourceCreateRequestOptions(BaseModel):
    """DID Linked Resource Create Request Schema."""
    did: str = Field(None, description="This input field indicates the DID that is the target of the DID Linked Resource create operation.")
    relativeDidUrl: Optional[str] = Field(None, description="This input field indicates a relative DID URL that is the target of the DID URL create operation.")
    content: str = Field(None, description="This input field contains Base64-encoded data that is the content of the resource associated with the DID URL.")
    name: str
    type: str
    version: Optional[str]

# ResourceUpdateRequestOptions Schema
class ResourceUpdateRequestOptions(ResourceCreateRequestOptions):
    """DID Linked Resource Update Request Schema."""
    pass

class BaseDIDRegistrar(ABC):
    """Base class for DID Registrars."""

    @abstractmethod
    async def create(self, options: DidCreateRequestOptions | SubmitSignatureOptions) -> dict:
        """Create a new DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update(self, options: DidUpdateRequestOptions | SubmitSignatureOptions) -> dict:
        """Update an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def deactivate(self, options: DidDeactivateRequestOptions | SubmitSignatureOptions) -> dict:
        """Deactivate an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def create_resource(self, did: str, options: ResourceCreateRequestOptions | SubmitSignatureOptions) -> dict:
        """Create a DID Linked Resource."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update_resource(self, did: str, options: ResourceUpdateRequestOptions | SubmitSignatureOptions) -> dict:
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
    async def create(self, did_doc: dict, options: dict = None) -> dict:
        """Create a new DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def update(self, did: str, did_doc: dict, options: dict = None) -> dict:
        """Update an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def deactivate(self, did: str, options: dict = None) -> dict:
        """Deactivate an existing DID."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    async def sign_requests(wallet: BaseWallet, signing_requests: list) -> List[SigningResponse]:
        """Sign all requests in the signing_requests list.

        Args:
            wallet: Wallet instance used to sign messages.
            signing_requests: List of signing request dictionaries.

        Returns:
            List of signed responses, each containing 'kid' and 'signature'.
        """
        signed_responses = []
        for sign_req in signing_requests:
            kid = sign_req.get("kid")
            payload_to_sign = sign_req.get("serializedPayload")
            # Retrieve verkey from wallet
            key = await wallet.get_key_by_kid(kid)
            if not key:
                raise ValueError(f"No key found for kid: {kid}")
            verkey = key.verkey
            # sign payload
            signature_bytes = await wallet.sign_message(
                b64_to_bytes(payload_to_sign), verkey
            )

            signed_responses.append(
                SigningResponse(
                    kid=kid,
                    signature=bytes_to_b64(signature_bytes),
                )
            )

        return signed_responses

    @staticmethod
    async def validate_did_doc(did_doc: dict) -> bool:
        """Validate the structure of the DID Document."""
        if not did_doc.get("id"):
            raise web.HTTPBadRequest(reason="DID Document must have an 'id'")
        # TODO Additional validation logic
        return True

    @staticmethod
    def format_response(
        success: bool, result: dict = None, error: str = None
    ) -> dict:
        """Format the response for operations."""
        return {
            "success": success,
            "result": result if success else None,
            "error": error if not success else None,
        }

class CheqdDIDManagerError(BaseError):
    """Base class for did cheqd manager exceptions."""