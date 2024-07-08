import pytest
import mockup_data
from typing import Any, Mapping, Optional
from typing import Any, Mapping
from pydid import DIDUrl

from aries_cloudagent.core.profile import Profile
from aries_cloudagent.wallet.default_verification_key_strategy import (
    BaseVerificationKeyStrategy,
)
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.util import b64_to_bytes, bytes_to_b64

import os
import json
import logging
import cbor2
from pycose.keys import CoseKey
from binascii import hexlify

from ...mso import MsoIssuer
from ...x509 import selfsigned_x509cert

LOGGER = logging.getLogger(__name__)
MDOC_TYPE = "org.iso.18013.5.1.mDL"
from mso_mdoc.v1_0.mso import MsoIssuer

def test_mso_issuer():
    jwk = {
            "kty" : "EC2",
            "crv" : "P_256",
            "x"   : "SVqB4JcUD6lsfvqMr-OKUNUphdNn64Eay60978ZlL74",
            "y"   : "lf0u0pMj4lGAzZix5u4Cm5CMQIgMNpkwy163wtKYVKI",
            "d"   : "0g5vAEKzugrXaRbgKG0Tj2qJ5lMP4Bezds1_sTybkfk"
    }

    pk_dict = {
        "KTY": jwk.get("kty") or "",  # OKP, EC
        "CURVE": jwk.get("crv") or "",  # ED25519, P_256
        "ALG": "EdDSA" if jwk.get("kty") == "OKP" else "ES256",
        "D": b64_to_bytes(jwk.get("d") or "", True),  # EdDSA
        "X": b64_to_bytes(jwk.get("x") or "", True),  # EdDSA, EcDSA
        "Y": b64_to_bytes(jwk.get("y") or "", True),  # EcDSA
        "KID": os.urandom(32),
    }

    cose_key = CoseKey.from_dict(pk_dict)
    if isinstance(payload, dict):
        data = [{"doctype": MDOC_TYPE, "data": payload}]
    documents = []
    for doc in data:
        _cert = selfsigned_x509cert(private_key=cose_key)
        msoi = MsoIssuer(data=doc["data"], private_key=cose_key, x509_cert=_cert)
        mso = msoi.sign(device_key=(headers.get("deviceKey") or ""), doctype=MDOC_TYPE)
        document = {
            "docType": MDOC_TYPE,
            "issuerSigned": {
                "nameSpaces": {
                    ns: [cbor2.CBORTag(24, value={k: v}) for k, v in dgst.items()]
                    for ns, dgst in msoi.disclosure_map.items()
                },
                "issuerAuth": mso.encode(),
            },
            # this is required during the presentation.
            #  'deviceSigned': {
            #  # TODO
            #  }
        }
        documents.append(document)

    signed = {
        "version": "1.0",
        "documents": documents,
        "status": 0,
    }
    signed_hex = hexlify(cbor2.dumps(signed))