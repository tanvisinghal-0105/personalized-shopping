"""
Pydantic data models for request/response validation.

Ensures type safety and data integrity across the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# -- Enums --


class ConsultationStage(str, Enum):
    ROOM_IDENTIFICATION = "stage_1_room_identification"
    ROOM_PURPOSE = "stage_1a_room_purpose"
    AGE_CONTEXT = "stage_1b_age_context"
    CONSTRAINTS = "stage_1c_constraints"
    PHOTO_REQUEST = "stage_1d_photo_request"
    STYLE_DISCOVERY = "stage_2_style_discovery"
    COLOR_PREFERENCES = "stage_3_color_preferences"
    ROOM_DIMENSIONS = "stage_4_room_dimensions"
    MOODBOARD_PRESENTED = "moodboard_presented"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FLAT = "flat"
    PRICE_MATCH = "price_match"
    BUNDLE = "bundle"


class EvalGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


# -- Cart Models --


class CartItem(BaseModel):
    product_id: str
    name: str = ""
    price: float = 0.0
    quantity: int = 1
    sku: str = ""


class Cart(BaseModel):
    cart_id: str = ""
    items: List[CartItem] = Field(default_factory=list)
    subtotal: float = 0.0


# -- Approval Models --


class ApprovalRequest(BaseModel):
    customer_id: str
    discount_type: DiscountType
    discount_value: float
    reason: str = ""
    product_id: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    cart_items: List[Dict[str, Any]] = Field(default_factory=list)
    cart_subtotal: float = 0.0
    discount_amount_eur: float = 0.0
    new_total_after_discount: float = 0.0


# -- Evaluation Models --


class EvalVerdict(BaseModel):
    question: str
    category: str
    severity: str
    verdict: str
    confidence: str = "LOW"
    explanation: str = ""
    score: Optional[float] = None


class ImageEvalResult(BaseModel):
    image_eval_score: float = 0.0
    blocker_failed: bool = False
    category_scores: Dict[str, float] = Field(default_factory=dict)
    verdicts: List[EvalVerdict] = Field(default_factory=list)
    criteria_count: int = 0
    verdicts_count: int = 0


class SessionEvalResult(BaseModel):
    session_id: str
    customer_id: str = "unknown"
    overall_score: float = 0.0
    grade: EvalGrade = EvalGrade.F
    trajectory_order_score: float = 0.0
    trajectory_args_score: float = 0.0
    step_skip_score: float = 0.0
    moodboard_quality_score: float = 0.0
    session_completion_score: float = 0.0
    speech_latency_score: float = 0.0
    speech_wer_score: float = 0.0
    image_quality: Optional[ImageEvalResult] = None


# -- Product Models --


class ProductSlim(BaseModel):
    """Slim product representation for context-efficient catalog."""

    product_id: str
    name: str
    category: str = ""
    subcategory: str = ""
    price: float = 0.0
    in_stock: bool = True
    image_url: str = ""
    style_tags: List[str] = Field(default_factory=list)
    color_palette: List[str] = Field(default_factory=list)
