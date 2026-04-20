#app/config/prompts.py
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """
你是一个专业的记账助手。
请将用户输入转换为结构化记账命令。

要求：
1. intent 固定为 add_record
2. category 只能是：饮食、工资、交通、购物、娱乐、房租、水电、其他
3. amount 支出为负数，收入为正数
4. remark 格式必须为：原句：<用户输入>
"""

FEW_SHOT = """
示例1：
用户：今天午饭花了18元
输出：{{"intent":"add_record","category":"饮食","amount":-18,"remark":"原句：今天午饭花了18元"}}

示例2：
用户：工资到账5000元
输出：{{"intent":"add_record","category":"工资","amount":5000,"remark":"原句：工资到账5000元"}}
"""

def build_prompt(format_instructions:str):
    safe_format_instructions = format_instructions.replace('{','{{').replace('}','}}')
    prompt = ChatPromptTemplate.from_messages([
        ("system",f"{SYSTEM_PROMPT}\n{FEW_SHOT}\n{safe_format_instructions}"),
        ("human","{user_text}")
    ])
    return prompt
