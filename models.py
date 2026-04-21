from pydantic import BaseModel


class UserAccountContext(BaseModel):

    customer_id: int
    name: str
    email: str
    tier: str = "basic"  # premium entreprise


class HandoffData(BaseModel):
    to_agent_name: str
    issue_type: str
    issue_description: str
    reason: str
