from unittest.mock import patch

from app.schemas.ai import AIParseResult
from app.services.ai.v1_3.ai_finance_service import (
    handle_add_record,
    handle_delete_record,
    handle_other_intent,
    handle_query_records,
)
from app.services.ai.v1_3.simple_agent import process_ai_request


def test_ai_parse_result_allows_none_remark_for_non_add_intents():
    result = AIParseResult(
        intent="query_records",
        category=None,
        amount=None,
        remark=None,
        year=2026,
        month=4,
        record_id=None,
    )

    assert result.remark is None


def test_handle_add_record_executes_successfully():
    cmd = AIParseResult(
        intent="add_record",
        category="饮食",
        amount=-18,
        remark="原句：今天午饭花了18元",
        year=None,
        month=None,
        record_id=None,
    )

    with patch("app.services.ai.v1_3.ai_finance_service.logger_info"), patch(
        "app.services.ai.v1_3.ai_finance_service.logger_error"
    ):
        tool = type("Tool", (), {"invoke": lambda _, payload: {"code": 200, "msg": "添加记账成功", "data": payload}})()
        result = handle_add_record(cmd, 1, tool)

    assert result["code"] == 200
    assert result["data"]["category"] == "饮食"


def test_handle_query_records_executes_successfully():
    cmd = AIParseResult(
        intent="query_records",
        category=None,
        amount=None,
        remark=None,
        year=2026,
        month=4,
        record_id=None,
    )

    with patch("app.services.ai.v1_3.ai_finance_service.logger_info"), patch(
        "app.services.ai.v1_3.ai_finance_service.logger_error"
    ):
        tool = type(
            "Tool",
            (),
            {
                "invoke": lambda _, payload: {
                    "code": 200,
                    "msg": "查询成功",
                    "data": payload,
                }
            },
        )()
        result = handle_query_records(cmd, 1, tool)

    assert result["code"] == 200
    assert result["data"]["year"] == 2026


def test_handle_delete_record_executes_successfully():
    cmd = AIParseResult(
        intent="delete_record",
        category=None,
        amount=None,
        remark=None,
        year=None,
        month=None,
        record_id=123,
    )

    with patch("app.services.ai.v1_3.ai_finance_service.logger_info"), patch(
        "app.services.ai.v1_3.ai_finance_service.logger_error"
    ):
        tool = type(
            "Tool",
            (),
            {
                "invoke": lambda _, payload: {
                    "code": 200,
                    "msg": "删除成功",
                    "data": payload,
                }
            },
        )()
        result = handle_delete_record(cmd, 1, tool)

    assert result["code"] == 200
    assert result["data"]["record_id"] == 123


def test_handle_other_intent_executes_successfully():
    cmd = AIParseResult(
        intent="other",
        category=None,
        amount=None,
        remark=None,
        year=None,
        month=None,
        record_id=None,
    )

    with patch("app.services.ai.v1_3.ai_finance_service.logger_info"):
        result = handle_other_intent(cmd)

    assert result == {
        "code": 200,
        "msg": "未识别的其他意图",
        "data": {"intent": "other"},
    }


def test_process_ai_request_dispatches_all_four_intents():
    cases = [
        (
            AIParseResult(
                intent="add_record",
                category="饮食",
                amount=-18,
                remark="原句：今天午饭花了18元",
                year=None,
                month=None,
                record_id=None,
            ),
            "app.services.ai.v1_3.simple_agent.handle_add_record",
        ),
        (
            AIParseResult(
                intent="query_records",
                category=None,
                amount=None,
                remark=None,
                year=2026,
                month=4,
                record_id=None,
            ),
            "app.services.ai.v1_3.simple_agent.handle_query_records",
        ),
        (
            AIParseResult(
                intent="delete_record",
                category=None,
                amount=None,
                remark=None,
                year=None,
                month=None,
                record_id=123,
            ),
            "app.services.ai.v1_3.simple_agent.handle_delete_record",
        ),
        (
            AIParseResult(
                intent="other",
                category=None,
                amount=None,
                remark=None,
                year=None,
                month=None,
                record_id=None,
            ),
            "app.services.ai.v1_3.simple_agent.handle_other_intent",
        ),
    ]

    with patch("app.services.ai.v1_3.simple_agent.logger_info"), patch(
        "app.services.ai.v1_3.simple_agent.logger_error"
    ):
        for cmd, handler_path in cases:
            with patch("app.services.ai.v1_3.simple_agent.parse_user_intent", return_value=cmd), patch(
                handler_path,
                return_value={"code": 200, "msg": cmd.intent, "data": {"intent": cmd.intent}},
            ) as mock_handler:
                result = process_ai_request("test", 1)

            mock_handler.assert_called_once()
            assert result["code"] == 200
            assert result["data"]["intent"] == cmd.intent
