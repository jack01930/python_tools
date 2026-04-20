"""
Tests for ai_record_service.py
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.schemas.ai import AIParseResult
from app.services.ai.ai_record_service import (
    call_qwen_api,
    ai_auto_record,
    clean_llm_json,
    get_langchain_llm,
    OpenAICompatibleLLMClient,
    PROMPT_TEMPLATE,
    llm_client
)


class TestCleanLlmJson:
    """Tests for clean_llm_json function"""

    def test_clean_llm_json_with_code_block(self):
        """Test cleaning JSON wrapped in code block markers"""
        content = '```json\n{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}\n```'
        result = clean_llm_json(content)
        assert result == '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'

    def test_clean_llm_json_with_prefix(self):
        """Test cleaning JSON with prefix text"""
        content = '解析结果：{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'
        result = clean_llm_json(content)
        assert result == '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'

    def test_clean_llm_json_with_quotes(self):
        """Test cleaning JSON wrapped in double quotes"""
        content = '"{\\"category\\":\\"饮食\\",\\"amount\\":-20,\\"remark\\":\\"原句：花20元吃面\\"}"'
        result = clean_llm_json(content)
        assert result == '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'

    def test_clean_llm_json_clean_input(self):
        """Test cleaning already clean JSON"""
        content = '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'
        result = clean_llm_json(content)
        assert result == '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'

    def test_clean_llm_json_with_whitespace(self):
        """Test cleaning JSON with leading/trailing whitespace"""
        content = '   {"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}   '
        result = clean_llm_json(content)
        assert result == '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'

    def test_clean_llm_json_no_brace(self):
        """Test cleaning content without braces"""
        content = 'some text without json'
        result = clean_llm_json(content)
        assert result == 'some text without json'


class TestCallQwenApi:
    """Tests for call_qwen_api function"""

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_success(self, mock_logger, mock_llm_client):
        """Test successful API call with valid JSON response"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("花20元吃面")

        assert isinstance(result, AIParseResult)
        assert result.category == "饮食"
        assert result.amount == -20
        assert result.remark == "原句：花20元吃面"
        mock_llm_client.chat_completions_create.assert_called_once()

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_with_quoted_json(self, mock_logger, mock_llm_client):
        """Test API call with JSON wrapped in quotes"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '"{\\"category\\":\\"交通\\",\\"amount\\":-50,\\"remark\\":\\"原句：打车花了50\\"}"'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("打车花了50")

        assert isinstance(result, AIParseResult)
        assert result.category == "交通"
        assert result.amount == -50

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_empty_remark(self, mock_logger, mock_llm_client):
        """Test API call with empty remark - should add default remark"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"工资","amount":5000,"remark":""}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("发工资5000")

        assert isinstance(result, AIParseResult)
        assert result.category == "工资"
        assert result.amount == 5000
        assert result.remark == "原句：发工资5000"

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_none_remark(self, mock_logger, mock_llm_client):
        """Test API call with None remark - should add default remark"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"购物","amount":-100}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("购物花了100")

        assert isinstance(result, AIParseResult)
        assert result.category == "购物"
        assert result.amount == -100
        assert result.remark == "原句：购物花了100"

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_call_qwen_api_invalid_json(self, mock_logger_error, mock_llm_client):
        """Test API call with invalid JSON response"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": 'invalid json'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            call_qwen_api("测试")

        assert "AI解析失败" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_call_qwen_api_missing_category(self, mock_logger_error, mock_llm_client):
        """Test API call with JSON missing category field"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"amount":-20,"remark":"test"}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            call_qwen_api("测试")

        assert "AI解析失败" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_call_qwen_api_api_exception(self, mock_logger_error, mock_llm_client):
        """Test API call when LLM client raises exception"""
        mock_llm_client.chat_completions_create.side_effect = Exception("API Error")

        with pytest.raises(ValueError) as exc_info:
            call_qwen_api("测试")

        assert "AI处理异常" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_call_qwen_api_secondary_parse_success(self, mock_logger_error, mock_logger_info, mock_llm_client):
        """Test secondary parse success after initial failure with category error"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '"{\\"category\\":\\"娱乐\\",\\"amount\\":-200,\\"remark\\":\\"原句：看电影\\"}"'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("看电影")

        assert isinstance(result, AIParseResult)
        assert result.category == "娱乐"

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_call_qwen_api_secondary_parse_failure(self, mock_logger_error, mock_llm_client):
        """Test when both initial and secondary parse fail"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '"invalid json with category word"'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            call_qwen_api("测试")

        assert "AI解析失败" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_with_code_block_response(self, mock_logger, mock_llm_client):
        """Test API call with code block wrapped response"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '```json\n{"category":"房租","amount":-2000,"remark":"原句：交房租"}\n```'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("交房租")

        assert isinstance(result, AIParseResult)
        assert result.category == "房租"
        assert result.amount == -2000

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_positive_amount(self, mock_logger, mock_llm_client):
        """Test API call with positive amount (income)"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"工资","amount":10000,"remark":"原句：收到工资"}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("收到工资")

        assert isinstance(result, AIParseResult)
        assert result.amount == 10000

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_zero_amount(self, mock_logger, mock_llm_client):
        """Test API call with zero amount"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"其他","amount":0,"remark":"原句：零元"}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("零元")

        assert isinstance(result, AIParseResult)
        assert result.amount == 0

    @patch('app.services.ai.ai_record_service.llm_client')
    @patch('app.services.ai.ai_record_service.logger_info')
    def test_call_qwen_api_float_amount(self, mock_logger, mock_llm_client):
        """Test API call with float amount"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"category":"饮食","amount":-25.5,"remark":"原句：花了25.5"}'
                }
            }]
        }
        mock_llm_client.chat_completions_create.return_value = mock_response

        result = call_qwen_api("花了25.5")

        assert isinstance(result, AIParseResult)
        assert result.amount == -25.5


class TestAiAutoRecord:
    """Tests for ai_auto_record function"""

    @patch('app.services.ai.ai_record_service.call_qwen_api')
    @patch('app.services.ai.ai_record_service.get_today_max_serial_num')
    @patch('app.services.ai.ai_record_service.add_finance_record')
    @patch('app.services.ai.ai_record_service.logger_info')
    @patch('app.services.ai.ai_record_service.datetime')
    def test_ai_auto_record_success(self, mock_datetime, mock_logger, mock_add_record, mock_get_serial, mock_call_api):
        """Test successful AI auto record"""
        mock_call_api.return_value = AIParseResult(
            category="饮食",
            amount=-20,
            remark="原句：花20元吃面"
        )
        mock_get_serial.return_value = 5
        mock_datetime.now.return_value.strftime.return_value = "2026-04-08"
        mock_add_record.return_value = {"id": 1, "status": "success"}

        result = ai_auto_record("花20元吃面", 123)

        assert "ai_parse_result" in result
        assert "record_detail" in result
        assert result["ai_parse_result"]["category"] == "饮食"
        mock_add_record.assert_called_once()

    @patch('app.services.ai.ai_record_service.call_qwen_api')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_ai_auto_record_api_failure(self, mock_logger_error, mock_call_api):
        """Test AI auto record when API call fails"""
        mock_call_api.side_effect = ValueError("AI解析失败")

        with pytest.raises(ValueError) as exc_info:
            ai_auto_record("测试", 123)

        assert "AI解析失败" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.call_qwen_api')
    @patch('app.services.ai.ai_record_service.get_today_max_serial_num')
    @patch('app.services.ai.ai_record_service.add_finance_record')
    @patch('app.services.ai.ai_record_service.logger_info')
    @patch('app.services.ai.ai_record_service.datetime')
    def test_ai_auto_record_first_record(self, mock_datetime, mock_logger, mock_add_record, mock_get_serial, mock_call_api):
        """Test AI auto record when it's the first record of the day (serial_num=0)"""
        mock_call_api.return_value = AIParseResult(
            category="交通",
            amount=-50,
            remark="原句：打车"
        )
        mock_get_serial.return_value = 0
        mock_datetime.now.return_value.strftime.return_value = "2026-04-08"
        mock_add_record.return_value = {"id": 1}

        result = ai_auto_record("打车", 123)

        assert result["record_detail"]["id"] == 1

    @patch('app.services.ai.ai_record_service.call_qwen_api')
    @patch('app.services.ai.ai_record_service.get_today_max_serial_num')
    @patch('app.services.ai.ai_record_service.add_finance_record')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_ai_auto_record_add_failure(self, mock_logger_error, mock_add_record, mock_get_serial, mock_call_api):
        """Test AI auto record when add_finance_record fails"""
        mock_call_api.return_value = AIParseResult(
            category="购物",
            amount=-100,
            remark="原句：买东西"
        )
        mock_get_serial.return_value = 1
        mock_add_record.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            ai_auto_record("买东西", 123)

        assert "Database error" in str(exc_info.value)


class TestOpenAICompatibleLLMClient:
    """Tests for OpenAICompatibleLLMClient class"""

    @patch('app.services.ai.ai_record_service.settings')
    def test_client_init(self, mock_settings):
        """Test client initialization with settings"""
        mock_settings.QWEN_API_KEY = "test_key"
        mock_settings.QWEN_BASE_URL = "http://test.com"
        mock_settings.QWEN_MODEL = "test_model"

        client = OpenAICompatibleLLMClient()

        assert client.api_key == "test_key"
        assert client.base_url == "http://test.com"
        assert client.model == "test_model"
        assert client.headers["Authorization"] == "Bearer test_key"

    @patch('app.services.ai.ai_record_service.requests.post')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_chat_completions_create_success(self, mock_logger_error, mock_post):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch('app.services.ai.ai_record_service.settings') as mock_settings:
            mock_settings.QWEN_API_KEY = "test_key"
            mock_settings.QWEN_BASE_URL = "http://test.com"
            mock_settings.QWEN_MODEL = "test_model"
            client = OpenAICompatibleLLMClient()

            result = client.chat_completions_create(
                messages=[{"role": "user", "content": "test"}],
                temperature=0.1,
                max_tokens=200
            )

            assert result == {"choices": [{"message": {"content": "test"}}]}
            mock_post.assert_called_once()

    @patch('app.services.ai.ai_record_service.requests.post')
    @patch('app.services.ai.ai_record_service.logger_error')
    def test_chat_completions_create_request_exception(self, mock_logger_error, mock_post):
        """Test chat completion with request exception"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with patch('app.services.ai.ai_record_service.settings') as mock_settings:
            mock_settings.QWEN_API_KEY = "test_key"
            mock_settings.QWEN_BASE_URL = "http://test.com"
            mock_settings.QWEN_MODEL = "test_model"
            client = OpenAICompatibleLLMClient()

            with pytest.raises(ValueError) as exc_info:
                client.chat_completions_create(messages=[{"role": "user", "content": "test"}])

            assert "LLM服务调用失败" in str(exc_info.value)

    @patch('app.services.ai.ai_record_service.requests.post')
    def test_chat_completions_create_default_params(self, mock_post):
        """Test chat completion with default parameters"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch('app.services.ai.ai_record_service.settings') as mock_settings:
            mock_settings.QWEN_API_KEY = "test_key"
            mock_settings.QWEN_BASE_URL = "http://test.com"
            mock_settings.QWEN_MODEL = "test_model"
            client = OpenAICompatibleLLMClient()

            client.chat_completions_create(messages=[{"role": "user", "content": "test"}])

            call_args = mock_post.call_args
            assert call_args[1]["json"]["temperature"] == 0.1
            assert call_args[1]["json"]["max_tokens"] == 200


class TestGetLangchainLlm:
    """Tests for get_langchain_llm function"""

    @patch('app.services.ai.ai_record_service.ChatOpenAI')
    @patch('app.services.ai.ai_record_service.settings')
    def test_get_langchain_llm(self, mock_settings, mock_chat_openai):
        """Test getting langchain LLM instance"""
        mock_settings.QWEN_API_KEY = "test_key"
        mock_settings.QWEN_BASE_URL = "http://test.com"
        mock_settings.QWEN_MODEL = "test_model"
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        result = get_langchain_llm()

        mock_chat_openai.assert_called_once_with(
            api_key="test_key",
            base_url="http://test.com",
            model_name="test_model",
            temperature=0.1
        )
        assert result == mock_instance


class TestPromptTemplate:
    """Tests for PROMPT_TEMPLATE"""

    def test_prompt_template_format(self):
        """Test that PROMPT_TEMPLATE can be formatted correctly"""
        user_text = "花20元吃面"
        formatted = PROMPT_TEMPLATE.format(user_text=user_text)

        assert user_text in formatted
        assert "category" in formatted
        assert "amount" in formatted
        assert "remark" in formatted

    def test_prompt_template_contains_rules(self):
        """Test that PROMPT_TEMPLATE contains required rules"""
        assert "饮食/工资/交通/购物/娱乐/房租/水电/其他" in PROMPT_TEMPLATE
        assert "支出为负数" in PROMPT_TEMPLATE
        assert "收入为正数" in PROMPT_TEMPLATE
        assert "原句：" in PROMPT_TEMPLATE
