import asyncio
from unittest import IsolatedAsyncioTestCase

from acapy_agent.connections.models.conn_record import ConnRecord
from acapy_agent.messaging.models.base import BaseModelError
from acapy_agent.protocols.coordinate_mediation.v1_0.route_manager import RouteManager
from acapy_agent.protocols.out_of_band.v1_0.manager import OutOfBandManager
from acapy_agent.tests import mock
from acapy_agent.utils.testing import create_test_profile

from ..exceptions import ConfigurationError, WitnessError
from ..witness_manager import WitnessManager


class TestWitnessManager(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.profile = await create_test_profile({"wallet.type": "askar-anoncreds"})

    @mock.patch.object(WitnessManager, "_get_active_witness_connection")
    async def test_auto_witness_setup_as_witness(
        self, mock_get_active_witness_connection
    ):
        self.profile.settings.set_value(
            "plugin_config",
            {"did-webvh": {"role": "witness"}},
        )
        await WitnessManager(self.profile).auto_witness_setup()
        assert not mock_get_active_witness_connection.called

    async def test_auto_witness_setup_as_controller_no_server_url(self):
        self.profile.settings.set_value(
            "plugin_config",
            {"did-webvh": {"role": "controller"}},
        )
        with self.assertRaises(ConfigurationError):
            await WitnessManager(self.profile).auto_witness_setup()

    async def test_auto_witness_setup_as_controller_with_previous_connection(self):
        self.profile.settings.set_value(
            "plugin_config",
            {"did-webvh": {"role": "controller", "server_url": "http://localhost:8000"}},
        )
        async with self.profile.session() as session:
            record = ConnRecord(
                alias="http://localhost:8000@Witness",
                state="active",
            )
            await record.save(session)
        await WitnessManager(self.profile).auto_witness_setup()

    async def test_auto_witness_setup_as_controller_no_witness_invitation(self):
        self.profile.settings.set_value(
            "plugin_config",
            {"did-webvh": {"role": "controller", "server_url": "http://localhost:8000"}},
        )
        await WitnessManager(self.profile).auto_witness_setup()

    @mock.patch.object(OutOfBandManager, "receive_invitation")
    async def test_auto_witness_setup_as_controller_bad_invitation(
        self, mock_receive_invitation
    ):
        self.profile.settings.set_value("plugin_config.did-webvh.role", "controller")
        self.profile.settings.set_value(
            "plugin_config",
            {
                "did-webvh": {
                    "role": "controller",
                    "server_url": "http://localhost:8000",
                    "witness_invitation": "http://localhost:9050?oob=eyJAdHlwZSI6ICJodHRwczovL2RpZGNvbW0ub3JnL291dC1vZi1iYW5kLzEuMS9pbnZpdGF0aW9uIiwgIkBpZCI6ICIwZDkwMGVjMC0wYzE3LTRmMTYtOTg1ZC1mYzU5MzVlYThjYTkiLCAibGFiZWwiOiAidGR3LWVuZG9yc2VyIiwgImhhbmRzaGFrZV9wcm90b2NvbHMiOiBbImh0dHBzOi8vZGlkY29tbS5vcmcvZGlkZXhjaGFuZ2UvMS4wIl0sICJzZXJ2aWNlcyI6IFt7ImlkIjogIiNpbmxpbmUiLCAidHlwZSI6ICJkaWQtY29tbXVuaWNhdGlvbiIsICJyZWNpcGllbnRLZXlzIjogWyJkaWQ6a2V5Ono2TWt0bXJUQURBWWRlc2Ftb3F1ZVV4NHNWM0g1Mms5b2ZoQXZRZVFaUG9vdTE3ZSN6Nk1rdG1yVEFEQVlkZXNhbW9xdWVVeDRzVjNINTJrOW9maEF2UWVRWlBvb3UxN2UiXSwgInNlcnZpY2VFbmRwb2ludCI6ICJodHRwOi8vbG9jYWxob3N0OjkwNTAifV19",
                }
            },
        )
        self.profile.context.injector.bind_instance(
            RouteManager, mock.AsyncMock(RouteManager, autospec=True)
        )
        mock_receive_invitation.side_effect = BaseModelError("Bad invitation")
        with self.assertRaises(WitnessError):
            await WitnessManager(self.profile).auto_witness_setup()

    @mock.patch.object(OutOfBandManager, "receive_invitation")
    @mock.patch.object(asyncio, "sleep")
    async def test_auto_witness_setup_as_controller_no_active_connection(self, *_):
        self.profile.settings.set_value("plugin_config.did-webvh.role", "controller")
        self.profile.settings.set_value(
            "plugin_config",
            {
                "did-webvh": {
                    "role": "controller",
                    "server_url": "http://localhost:8000",
                    "witness_invitation": "http://localhost:9050?oob=eyJAdHlwZSI6ICJodHRwczovL2RpZGNvbW0ub3JnL291dC1vZi1iYW5kLzEuMS9pbnZpdGF0aW9uIiwgIkBpZCI6ICIwZDkwMGVjMC0wYzE3LTRmMTYtOTg1ZC1mYzU5MzVlYThjYTkiLCAibGFiZWwiOiAidGR3LWVuZG9yc2VyIiwgImhhbmRzaGFrZV9wcm90b2NvbHMiOiBbImh0dHBzOi8vZGlkY29tbS5vcmcvZGlkZXhjaGFuZ2UvMS4wIl0sICJzZXJ2aWNlcyI6IFt7ImlkIjogIiNpbmxpbmUiLCAidHlwZSI6ICJkaWQtY29tbXVuaWNhdGlvbiIsICJyZWNpcGllbnRLZXlzIjogWyJkaWQ6a2V5Ono2TWt0bXJUQURBWWRlc2Ftb3F1ZVV4NHNWM0g1Mms5b2ZoQXZRZVFaUG9vdTE3ZSN6Nk1rdG1yVEFEQVlkZXNhbW9xdWVVeDRzVjNINTJrOW9maEF2UWVRWlBvb3UxN2UiXSwgInNlcnZpY2VFbmRwb2ludCI6ICJodHRwOi8vbG9jYWxob3N0OjkwNTAifV19",
                }
            },
        )
        self.profile.context.injector.bind_instance(
            RouteManager, mock.AsyncMock(RouteManager, autospec=True)
        )
        await WitnessManager(self.profile).auto_witness_setup()

    @mock.patch.object(OutOfBandManager, "receive_invitation")
    async def test_auto_witness_setup_as_controller_conn_becomes_active(self, *_):
        self.profile.settings.set_value("plugin_config.did-webvh.role", "controller")
        self.profile.settings.set_value(
            "plugin_config",
            {
                "did-webvh": {
                    "role": "controller",
                    "server_url": "http://localhost:8000",
                    "witness_invitation": "http://localhost:9050?oob=eyJAdHlwZSI6ICJodHRwczovL2RpZGNvbW0ub3JnL291dC1vZi1iYW5kLzEuMS9pbnZpdGF0aW9uIiwgIkBpZCI6ICIwZDkwMGVjMC0wYzE3LTRmMTYtOTg1ZC1mYzU5MzVlYThjYTkiLCAibGFiZWwiOiAidGR3LWVuZG9yc2VyIiwgImhhbmRzaGFrZV9wcm90b2NvbHMiOiBbImh0dHBzOi8vZGlkY29tbS5vcmcvZGlkZXhjaGFuZ2UvMS4wIl0sICJzZXJ2aWNlcyI6IFt7ImlkIjogIiNpbmxpbmUiLCAidHlwZSI6ICJkaWQtY29tbXVuaWNhdGlvbiIsICJyZWNpcGllbnRLZXlzIjogWyJkaWQ6a2V5Ono2TWt0bXJUQURBWWRlc2Ftb3F1ZVV4NHNWM0g1Mms5b2ZoQXZRZVFaUG9vdTE3ZSN6Nk1rdG1yVEFEQVlkZXNhbW9xdWVVeDRzVjNINTJrOW9maEF2UWVRWlBvb3UxN2UiXSwgInNlcnZpY2VFbmRwb2ludCI6ICJodHRwOi8vbG9jYWxob3N0OjkwNTAifV19",
                }
            },
        )
        self.profile.context.injector.bind_instance(
            RouteManager, mock.AsyncMock(RouteManager, autospec=True)
        )

        async def _create_connection():
            await asyncio.sleep(1)
            async with self.profile.session() as session:
                record = ConnRecord(
                    alias="http://localhost:8000@Witness",
                    state="active",
                )
                await record.save(session)

        asyncio.create_task(_create_connection())
        await WitnessManager(self.profile).auto_witness_setup()
