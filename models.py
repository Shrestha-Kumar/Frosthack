from typing import TypedDict, List, Optional, Literal, Annotated
from pydantic import BaseModel
import operator

class CustomerProfile(BaseModel):
    customer_id: str
    age: int
    gender: str
    status: str
    employment: Optional[str] = None
    location: Optional[str] = None

class MicroSegment(BaseModel):
    segment_id: str
    name: str
    customer_ids: List[str]
    strategy_notes: str
    psychological_hook: str
    recommended_tone: str
    recommended_send_time: str 

class EmailVariant(BaseModel):
    variant_id: str
    segment_id: str
    subject: str 
    body_html: str 
    tone: str
    has_emoji: bool
    emoji_positions: List[str] 
    url_included: bool
    url_position: Optional[str]
    bold_elements: List[str]
    italic_elements: List[str]

class PerformanceReport(BaseModel):
    campaign_id: str
    variant_id: str
    segment_id: str
    open_rate: float
    click_rate: float
    composite_score: float 
    fetched_at: str 

class OptimizationRecord(BaseModel):
    iteration: int
    insight: str 
    action_taken: str
    variants_changed: List[str]
    segments_retargeted: List[str]

class ParsedBrief(BaseModel):
    product_name: str
    product_description: str
    base_return_advantage: str
    special_offers: List[str] 
    optimization_targets: List[str] 
    include_inactive: bool 
    cta_url: str
    additional_instructions: List[str]

class ToolDefinition(BaseModel):
    name: str
    description: str
    endpoint: str
    method: str
    parameters_schema: dict

class CampaignState(TypedDict):
    raw_brief: str
    parsed_brief: Optional[ParsedBrief]
    full_cohort: List[CustomerProfile]
    active_segments: List[MicroSegment]
    current_variants: List[EmailVariant]
    approved_variants: List[EmailVariant]
    scheduled_campaign_ids: Annotated[List[str], operator.add]
    performance_reports: Annotated[List[PerformanceReport], operator.add]
    hitl_status: Literal["not_started", "pending", "approved", "rejected"]
    hitl_feedback: Optional[str]
    iteration_count: int
    max_iterations: int 
    optimization_history: Annotated[List[OptimizationRecord], operator.add]
    should_continue_optimization: bool
    openapi_spec: Optional[dict]
    discovered_tools: List[ToolDefinition]
    api_error_log: List[str]
    messages: Annotated[List[dict], operator.add]