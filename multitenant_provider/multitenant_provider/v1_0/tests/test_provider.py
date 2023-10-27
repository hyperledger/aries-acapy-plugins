import asynctest
from aries_cloudagent.config.base import InjectionError
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.utils.classloader import ClassLoader, ClassNotFoundError
from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock

from multitenant_provider.v1_0.config import MultitenantProviderConfig

from ..provider import CustomMultitenantManagerProvider


class TestProvider(AsyncTestCase):
    async def setUp(self) -> None:
        self.profile = InMemoryProfile.test_profile()
        self.profile.inject = async_mock.Mock()
        self.profile.inject.return_value = MultitenantProviderConfig(
            manager={"class_name": "test-class-name"}
        )

    @asynctest.patch.object(ClassLoader, "load_class")
    async def test_provide_loads_manager(self, mock_class_loader):
        mock_class_loader.return_value = lambda _: {"test-class-name": "manager"}
        provider = CustomMultitenantManagerProvider(self.profile)
        result = provider.provide({}, {})
        assert result["test-class-name"] == "manager"

    @asynctest.patch.object(ClassLoader, "load_class")
    async def test_provide_raises_error_when_loading_class_fails(
        self, mock_class_loader
    ):
        mock_class_loader.return_value = lambda _: (_ for _ in ()).throw(
            ClassNotFoundError("test-message")
        )
        provider = CustomMultitenantManagerProvider(self.profile)
        with self.assertRaises(InjectionError):
            provider.provide({}, {})
