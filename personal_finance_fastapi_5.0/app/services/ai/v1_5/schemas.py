from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class AgentAction(BaseModel):
    action: Literal["tool_call", "clarify", "respond", "fail"] = Field(
        ...,
        description="Agent下一步动作类型",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="当action=tool_call时要调用的工具名",
    )
    tool_input: dict[str, Any] = Field(
        default_factory=dict,
        description="工具调用参数",
    )
    message: Optional[str] = Field(
        default=None,
        description="当action为clarify/respond/fail时给用户或系统的消息",
    )

    @model_validator(mode="after")
    def validate_action(self) -> "AgentAction":
        if self.action == "tool_call" and not self.tool_name:
            raise ValueError("tool_call 动作必须包含 tool_name")
        if self.action in {"clarify", "respond", "fail"} and not self.message:
            raise ValueError(f"{self.action} 动作必须包含 message")
        return self


class AgentPlannerOutput(BaseModel):
    thought: str = Field(..., description="当前这一步的思考摘要")
    action: AgentAction = Field(..., description="下一步动作")


class AgentStep(BaseModel):
    step_no: int = Field(..., description="当前是第几步")
    thought: str = Field(..., description="当前步骤的思考摘要")
    action: str = Field(..., description="动作类型")
    tool_name: Optional[str] = Field(default=None, description="被调用的工具")
    tool_input: dict[str, Any] = Field(default_factory=dict, description="工具参数")
    observation: Optional[dict[str, Any]] = Field(default=None, description="工具返回结果")
    message: Optional[str] = Field(default=None, description="clarify/respond/fail时的消息")


class AgentState(BaseModel):
    user_id: int = Field(..., description="用户ID")
    user_text: str = Field(..., description="用户本轮输入")
    history: list[dict[str, Any]] = Field(default_factory=list, description="预留的短期上下文")
    steps: list[AgentStep] = Field(default_factory=list, description="本轮执行过的所有步骤")
    max_steps: int = Field(default=3, ge=1, le=8, description="最大执行步数")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="元数据，如会话ID、已填槽位等")


class AgentResponse(BaseModel):
    reply: str = Field(..., description="最终返回给用户的自然语言回复")