import asynctest
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.storage.error import StorageDuplicateError, StorageNotFoundError
from asynctest import TestCase as AsyncTestCase

from ..models import WalletTokenRecord


class TestModels(AsyncTestCase):
    def setUp(self) -> None:
        self.profile = InMemoryProfile.test_profile()

    @asynctest.patch.object(
        WalletTokenRecord,
        "query",
        return_value=["test-wallet"],
    )
    async def test_query_by_wallet_id_returns_one_record(self, mock_query):
        wallet_token_record = WalletTokenRecord()
        found_token_record = await wallet_token_record.query_by_wallet_id(
            session=self.profile.session, wallet_id="wallet-id"
        )
        assert mock_query.called
        assert found_token_record == "test-wallet"

    @asynctest.patch.object(
        WalletTokenRecord,
        "query",
        return_value=["test-wallet-1", "test-wallet-2"],
    )
    async def test_query_by_wallet_id_raises_duplicate_error_when_multiple_records(
        self, mock_query
    ):
        wallet_token_record = WalletTokenRecord()
        with self.assertRaises(StorageDuplicateError):
            await wallet_token_record.query_by_wallet_id(
                session=self.profile.session, wallet_id="wallet-id"
            )
            assert mock_query.called

    @asynctest.patch.object(
        WalletTokenRecord,
        "query",
        return_value=[],
    )
    async def test_query_by_wallet_id_raises_not_found_error_when_finds_no_records(
        self, mock_query
    ):
        wallet_token_record = WalletTokenRecord()
        with self.assertRaises(StorageNotFoundError):
            await wallet_token_record.query_by_wallet_id(
                session=self.profile.session, wallet_id="wallet-id"
            )
            assert mock_query.called
