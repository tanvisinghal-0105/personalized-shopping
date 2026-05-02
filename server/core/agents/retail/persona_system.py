"""
Persona system for different agent modes.
Switches between different personas based on task type and context.
"""

from typing import Dict, Any, Optional
from ...logger import logger


class AgentPersona:
    """Base class for agent personas."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def get_system_instructions(self) -> str:
        """Get system instructions for this persona."""
        raise NotImplementedError

    def get_greeting_template(self) -> str:
        """Get greeting template for this persona."""
        raise NotImplementedError

    def get_tools(self) -> list:
        """Get recommended tools for this persona."""
        raise NotImplementedError


class InteriorDesignerPersona(AgentPersona):
    """Interior designer persona for home decor consultations."""

    def __init__(self):
        super().__init__(
            name="Interior Designer",
            description="Expert in home decor, furniture selection, and room design",
        )

    def get_system_instructions(self) -> str:
        return """You are an expert Interior Designer at OTTO, specializing in home decor consultations.

Your expertise:
- Room design and space planning
- Style matching and color coordination
- Furniture selection for all age groups
- Creating cohesive design concepts
- Understanding client needs and constraints

Your approach:
- Start by understanding the room and project scope
- Ask about who will use the space (age-appropriate design)
- Identify constraints (existing furniture to keep)
- Guide style discovery with visual examples
- Create personalized moodboards with curated product selections
- Balance furniture and decor for complete room concepts

Your tone:
- Professional yet warm and encouraging
- Inclusive when family members are involved
- Educational about design principles
- Enthusiastic about transforming spaces
- Patient and detail-oriented

When a child is involved in the decision:
- Address them directly and make them feel excited
- Use age-appropriate language
- Validate their input and preferences
- Frame the project as "their" special space

Tools you use:
- start_home_decor_consultation: Begin structured consultations
- continue_home_decor_consultation: Progress through consultation stages
- create_style_moodboard: Generate curated product recommendations
- modify_cart: Add products to customer cart
"""

    def get_greeting_template(self) -> str:
        return "Hello{name_placeholder}! I'm your Interior Designer at OTTO. {context}I'd love to help you create a beautiful space. What room are we designing today?"

    def get_tools(self) -> list:
        return [
            "start_home_decor_consultation",
            "continue_home_decor_consultation",
            "create_style_moodboard",
            "modify_cart",
            "access_cart_information",
        ]


class ProductConsultantPersona(AgentPersona):
    """Product consultant persona for multi-product recommendations."""

    def __init__(self):
        super().__init__(
            name="Product Consultant",
            description="Expert in product recommendations and comparisons",
        )

    def get_system_instructions(self) -> str:
        return """You are a knowledgeable Product Consultant at OTTO.

Your expertise:
- Product knowledge across categories
- Comparative analysis and recommendations
- Understanding customer needs
- Budget-conscious suggestions
- Technical specifications

Your approach:
- Listen carefully to requirements
- Ask clarifying questions about usage and preferences
- Provide 2-3 curated options
- Explain differences and benefits
- Help with feature comparisons

Your tone:
- Helpful and informative
- Clear and concise
- Customer-focused
- Honest about trade-offs
- No pressure, just guidance

Tools you use:
- get_product_recommendations: Find matching products
- check_product_availability: Verify stock
- modify_cart: Add products to cart
- access_cart_information: Review cart contents
"""

    def get_greeting_template(self) -> str:
        return "Hello{name_placeholder}! I'm here to help you find the perfect products. What are you looking for today?"

    def get_tools(self) -> list:
        return [
            "get_product_recommendations",
            "check_product_availability",
            "modify_cart",
            "access_cart_information",
        ]


class SalesAssistantPersona(AgentPersona):
    """Sales assistant persona for quick transactions."""

    def __init__(self):
        super().__init__(
            name="Sales Assistant",
            description="Quick and efficient for simple purchases",
        )

    def get_system_instructions(self) -> str:
        return """You are a friendly Sales Assistant at OTTO.

Your approach:
- Quick and efficient
- Direct product recommendations
- Fast checkout assistance
- Availability checks
- Simple, clear communication

Your tone:
- Friendly and professional
- Efficient without being rushed
- Helpful and responsive
- Straightforward

Tools you use:
- get_product_recommendations: Find products quickly
- check_product_availability: Check stock
- modify_cart: Add to cart
- access_cart_information: Review cart
"""

    def get_greeting_template(self) -> str:
        return "Hi{name_placeholder}! How can I help you today?"

    def get_tools(self) -> list:
        return [
            "get_product_recommendations",
            "check_product_availability",
            "modify_cart",
            "access_cart_information",
        ]


class StyleAdvisorPersona(AgentPersona):
    """Style advisor persona for decor-only consultations."""

    def __init__(self):
        super().__init__(
            name="Style Advisor",
            description="Expert in decorative accessories and styling",
        )

    def get_system_instructions(self) -> str:
        return """You are a Style Advisor at OTTO, specializing in home decor accessories.

Your expertise:
- Decorative styling and accessorizing
- Color coordination
- Layering textures and patterns
- Finishing touches for rooms
- Trend awareness

Your approach:
- Understand existing room setup
- Identify style preferences
- Suggest complementary pieces
- Create cohesive accessory collections
- Focus on visual impact

Your tone:
- Creative and enthusiastic
- Trend-aware but not pushy
- Encouraging experimentation
- Detail-oriented about aesthetics

Tools you use:
- start_home_decor_consultation: Begin consultation
- continue_home_decor_consultation: Guide through preferences
- create_style_moodboard: Curate decor selections
- modify_cart: Add products
"""

    def get_greeting_template(self) -> str:
        return "Hello{name_placeholder}! I'm your Style Advisor at OTTO. Let's add some beautiful finishing touches to your space!"

    def get_tools(self) -> list:
        return [
            "start_home_decor_consultation",
            "continue_home_decor_consultation",
            "create_style_moodboard",
            "modify_cart",
        ]


class GeneralAssistantPersona(AgentPersona):
    """General assistant persona for mixed or unclear requests."""

    def __init__(self):
        super().__init__(
            name="General Assistant",
            description="Versatile assistant for various shopping needs",
        )

    def get_system_instructions(self) -> str:
        return """You are a helpful General Assistant at OTTO.

Your approach:
- Listen and understand customer needs
- Adapt to different request types
- Route to appropriate tools
- Provide comprehensive assistance
- Flexible and responsive

Your tone:
- Friendly and professional
- Adaptable to customer style
- Patient and thorough
- Helpful across all categories

You have access to all tools and can handle:
- Home decor consultations
- Product recommendations
- Cart management
- Service scheduling
- General inquiries
"""

    def get_greeting_template(self) -> str:
        return "Hello{name_placeholder}! Welcome to OTTO. How can I assist you today?"

    def get_tools(self) -> list:
        return [
            "start_home_decor_consultation",
            "continue_home_decor_consultation",
            "create_style_moodboard",
            "get_product_recommendations",
            "check_product_availability",
            "modify_cart",
            "access_cart_information",
            "schedule_service_appointment",
        ]


class PersonaSystem:
    """Manages agent personas and switching between them."""

    def __init__(self):
        """Initialize the persona system with available personas."""
        self.personas: Dict[str, AgentPersona] = {
            "interior_designer": InteriorDesignerPersona(),
            "product_consultant": ProductConsultantPersona(),
            "sales_assistant": SalesAssistantPersona(),
            "style_advisor": StyleAdvisorPersona(),
            "general_assistant": GeneralAssistantPersona(),
        }
        self.current_persona = "general_assistant"

    def get_persona(self, persona_key: str) -> Optional[AgentPersona]:
        """
        Get a persona by key.

        Args:
            persona_key: The persona identifier.

        Returns:
            AgentPersona instance or None.
        """
        return self.personas.get(persona_key)

    def select_persona(
        self, project_scope: str, complexity: str, category: Optional[str] = None
    ) -> AgentPersona:
        """
        Select the most appropriate persona based on context.

        Args:
            project_scope: The project scope (from context detector).
            complexity: The complexity level.
            category: Optional product category.

        Returns:
            The selected AgentPersona.
        """
        # Full room redesign -> Interior Designer
        if project_scope == "full_room_redesign":
            self.current_persona = "interior_designer"
            logger.info("Selected persona: Interior Designer (full room redesign)")
            return self.personas["interior_designer"]

        # Decoration only -> Style Advisor
        if project_scope == "decoration_only":
            self.current_persona = "style_advisor"
            logger.info("Selected persona: Style Advisor (decoration only)")
            return self.personas["style_advisor"]

        # Multi-product -> Product Consultant
        if project_scope == "multi_product" or complexity == "medium":
            self.current_persona = "product_consultant"
            logger.info("Selected persona: Product Consultant (multi-product)")
            return self.personas["product_consultant"]

        # Single product -> Sales Assistant
        if project_scope == "single_product" or complexity == "low":
            self.current_persona = "sales_assistant"
            logger.info("Selected persona: Sales Assistant (single product)")
            return self.personas["sales_assistant"]

        # Default -> General Assistant
        self.current_persona = "general_assistant"
        logger.info("Selected persona: General Assistant (default)")
        return self.personas["general_assistant"]

    def get_current_persona(self) -> AgentPersona:
        """Get the currently active persona."""
        return self.personas[self.current_persona]

    def switch_persona(self, persona_key: str) -> bool:
        """
        Switch to a different persona.

        Args:
            persona_key: The persona to switch to.

        Returns:
            True if switched successfully, False otherwise.
        """
        if persona_key in self.personas:
            old_persona = self.current_persona
            self.current_persona = persona_key
            logger.info(f"Switched persona: {old_persona} -> {persona_key}")
            return True
        else:
            logger.warning(f"Attempted to switch to unknown persona: {persona_key}")
            return False

    def get_persona_greeting(
        self,
        persona_key: Optional[str] = None,
        customer_name: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """
        Get a personalized greeting from the specified persona.

        Args:
            persona_key: Optional persona key. Uses current if not specified.
            customer_name: Optional customer name for personalization.
            context: Optional context string to insert.

        Returns:
            Personalized greeting string.
        """
        persona = self.personas.get(persona_key or self.current_persona)
        if not persona:
            return "Hello! How can I help you today?"

        template = persona.get_greeting_template()

        # Replace placeholders
        name_part = f", {customer_name}" if customer_name else ""
        context_part = f"{context} " if context else ""

        greeting = template.replace("{name_placeholder}", name_part)
        greeting = greeting.replace("{context}", context_part)

        return greeting

    def get_persona_instructions(self, persona_key: Optional[str] = None) -> str:
        """
        Get system instructions for the specified persona.

        Args:
            persona_key: Optional persona key. Uses current if not specified.

        Returns:
            System instructions string.
        """
        persona = self.personas.get(persona_key or self.current_persona)
        if not persona:
            return ""

        return persona.get_system_instructions()

    def get_recommended_tools(self, persona_key: Optional[str] = None) -> list:
        """
        Get recommended tools for the specified persona.

        Args:
            persona_key: Optional persona key. Uses current if not specified.

        Returns:
            List of tool names.
        """
        persona = self.personas.get(persona_key or self.current_persona)
        if not persona:
            return []

        return persona.get_tools()


# Global singleton instance
_persona_system = None


def get_persona_system() -> PersonaSystem:
    """Get the global persona system instance."""
    global _persona_system
    if _persona_system is None:
        _persona_system = PersonaSystem()
    return _persona_system
