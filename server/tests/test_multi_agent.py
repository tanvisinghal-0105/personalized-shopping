"""Tests for ADK multi-agent structure."""

import pytest


class TestMultiAgentStructure:
    """Verify the multi-agent architecture is correctly wired."""

    def test_sub_agent_functions_exist(self):
        """Verify sub-agent constructor functions exist."""
        from core.agents.retail.agent import (
            _create_shopping_agent,
            _create_home_decor_agent,
            _create_services_agent,
        )

        assert callable(_create_shopping_agent)
        assert callable(_create_home_decor_agent)
        assert callable(_create_services_agent)

    def test_root_agent_instruction_exists(self):
        """Verify the root orchestrator instruction is defined."""
        from core.agents.retail.agent import ROOT_AGENT_INSTRUCTION

        assert "shopping_agent" in ROOT_AGENT_INSTRUCTION
        assert "home_decor_agent" in ROOT_AGENT_INSTRUCTION
        assert "services_agent" in ROOT_AGENT_INSTRUCTION

    def test_shopping_agent_has_correct_tools(self):
        """Verify shopping agent has the expected tools."""
        from core.agents.retail.agent import SHOPPING_AGENT_INSTRUCTION

        assert "access_cart_information" in SHOPPING_AGENT_INSTRUCTION
        assert "modify_cart" in SHOPPING_AGENT_INSTRUCTION
        assert "sync_ask_for_approval" in SHOPPING_AGENT_INSTRUCTION

    def test_home_decor_agent_has_correct_tools(self):
        """Verify home decor agent has the expected tools."""
        from core.agents.retail.agent import HOME_DECOR_AGENT_INSTRUCTION

        assert "start_home_decor_consultation" in HOME_DECOR_AGENT_INSTRUCTION
        assert "continue_home_decor_consultation" in HOME_DECOR_AGENT_INSTRUCTION
        assert "create_style_moodboard" in HOME_DECOR_AGENT_INSTRUCTION

    def test_services_agent_has_correct_tools(self):
        """Verify services agent has the expected tools."""
        from core.agents.retail.agent import SERVICES_AGENT_INSTRUCTION

        assert "lookup_warranty_details" in SERVICES_AGENT_INSTRUCTION
        assert "get_trade_in_value" in SERVICES_AGENT_INSTRUCTION
        assert "schedule_service_appointment" in SERVICES_AGENT_INSTRUCTION

    def test_safety_settings_defined(self):
        """Verify safety settings are in the generation config."""
        from core.agents.retail.agent import _make_gen_config

        config = _make_gen_config()
        assert config.safety_settings is not None
        assert len(config.safety_settings) == 4

    def test_identify_phone_in_shopping_agent(self):
        """Verify identify_phone_from_camera_feed is available."""
        from core.agents.retail.tools import identify_phone_from_camera_feed

        assert callable(identify_phone_from_camera_feed)


class TestToolImports:
    """Verify all tools are importable."""

    def test_all_shopping_tools(self):
        from core.agents.retail.tools import (
            access_cart_information,
            modify_cart,
            identify_phone_from_camera_feed,
            get_product_recommendations,
            check_product_availability,
            display_product_search_results,
            sync_ask_for_approval,
        )

    def test_all_home_decor_tools(self):
        from core.agents.retail.tools import (
            start_home_decor_consultation,
            continue_home_decor_consultation,
            create_style_moodboard,
            analyze_room_for_decor,
            analyze_room_with_history,
            analyze_room_photos_batch,
            get_customer_order_history,
            visualize_room_with_products,
        )

    def test_all_services_tools(self):
        from core.agents.retail.tools import (
            lookup_warranty_details,
            get_trade_in_value,
            schedule_service_appointment,
            get_available_service_times,
            process_exchange_request,
            generate_qr_code,
            send_call_companion_link,
        )
