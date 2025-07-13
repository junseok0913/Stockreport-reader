"""
Supervisor Agent 구현
사용자 질문 분석 및 워커 에이전트 조정
LangGraph 공식 Tool-calling Supervisor 패턴 적용 (OpenAI 전용)
"""

import os
from typing import Dict, Any, List, Annotated
from datetime import datetime, timedelta
from langchain.tools import BaseTool, tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent, InjectedState

from .prompt import SUPERVISOR_PROMPT
from ..shared.state import MessagesState


class SupervisorAgent:
    """
    Supervisor Agent (LangGraph 공식 Tool-calling Supervisor 패턴)
    사용자의 질문을 분석하고 Stock Price Agent를 조정하여 최종 답변을 생성
    모든 Agent에서 OpenAI 사용
    """
    
    def __init__(self, supervisor_llm: ChatOpenAI, stock_llm: ChatOpenAI):
        """
        Supervisor Agent 초기화
        
        Args:
            supervisor_llm: Supervisor용 ChatOpenAI 인스턴스
            stock_llm: Stock Price Agent용 ChatOpenAI 인스턴스
        """
        self.supervisor_llm = supervisor_llm
        self.stock_llm = stock_llm
        
        # Stock Price Agent 인스턴스를 지연 로딩으로 생성
        self._stock_price_agent = None
        
        # Stock Price Agent 툴 정의 (공식 패턴)
        self.stock_price_tool = self._create_stock_price_tool()
        
        # 정확한 날짜 정보 계산
        date_info = self._calculate_date_info()
        
        # tools와 tool_names 정보 추가
        tools_info = self._get_tools_info([self.stock_price_tool])
        
        # 모든 포맷팅 정보 결합
        format_info = {**date_info, **tools_info}
        
        # 프롬프트 포맷팅
        formatted_prompt = SUPERVISOR_PROMPT.format(**format_info)
        
        # LangGraph React Agent 생성 (표준 Tool-calling Supervisor 패턴)
        # Supervisor는 OpenAI 사용
        self.agent = create_react_agent(
            self.supervisor_llm,
            tools=[self.stock_price_tool],
            prompt=formatted_prompt
        )
    
    def _calculate_date_info(self) -> Dict[str, str]:
        """Python datetime.now()로 정확한 날짜 정보를 계산합니다"""
        today = datetime.now()
        
        # 기본 날짜들
        today_date = today.strftime('%Y%m%d')
        yesterday_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        tomorrow_date = (today + timedelta(days=1)).strftime('%Y%m%d')
        
        # 이번달
        this_month_start = today.replace(day=1).strftime('%Y%m%d')
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        this_month_end = (next_month - timedelta(days=1)).strftime('%Y%m%d')
        
        # 지난달
        if today.month == 1:
            last_month_start = today.replace(year=today.year - 1, month=12, day=1).strftime('%Y%m%d')
            this_month_first = today.replace(day=1)
            last_month_end = (this_month_first - timedelta(days=1)).strftime('%Y%m%d')
        else:
            last_month_start = today.replace(month=today.month - 1, day=1).strftime('%Y%m%d')
            this_month_first = today.replace(day=1)
            last_month_end = (this_month_first - timedelta(days=1)).strftime('%Y%m%d')
        
        # 다음달
        next_month_start = next_month.strftime('%Y%m%d')
        if next_month.month == 12:
            next_next_month = next_month.replace(year=next_month.year + 1, month=1, day=1)
        else:
            next_next_month = next_month.replace(month=next_month.month + 1, day=1)
        next_month_end = (next_next_month - timedelta(days=1)).strftime('%Y%m%d')
        
        # 올해/작년
        this_year_start = today.replace(month=1, day=1).strftime('%Y%m%d')
        this_year_end = today.replace(month=12, day=31).strftime('%Y%m%d')
        last_year_start = today.replace(year=today.year - 1, month=1, day=1).strftime('%Y%m%d')
        last_year_end = today.replace(year=today.year - 1, month=12, day=31).strftime('%Y%m%d')
        
        return {
            'today_date': today_date,
            'yesterday_date': yesterday_date,
            'tomorrow_date': tomorrow_date,
            'this_month_start': this_month_start,
            'this_month_end': this_month_end,
            'last_month_start': last_month_start,
            'last_month_end': last_month_end,
            'next_month_start': next_month_start,
            'next_month_end': next_month_end,
            'this_year_start': this_year_start,
            'this_year_end': this_year_end,
            'last_year_start': last_year_start,
            'last_year_end': last_year_end,
            'current_year': str(today.year),
            'last_year': str(today.year - 1)
        }
    
    def _get_tools_info(self, tools: List[BaseTool]) -> Dict[str, str]:
        """tools 정보를 prompt에 사용할 수 있는 형태로 변환합니다"""
        # tools 설명 생성
        tools_desc = []
        tool_names = []
        
        for tool in tools:
            tool_names.append(tool.name)
            tool_desc = f"- **{tool.name}**: {tool.description}"
            tools_desc.append(tool_desc)
        
        return {
            'tools': '\n'.join(tools_desc),
            'tool_names': ', '.join(tool_names)
        }
    
    @property
    def stock_price_agent(self):
        """Stock Price Agent 인스턴스를 지연 로딩합니다 (순환 import 방지)"""
        if self._stock_price_agent is None:
            from ..stock_price_agent.agent import StockPriceAgent
            # Stock Price Agent는 stock_llm 사용 (OpenAI)
            self._stock_price_agent = StockPriceAgent(self.stock_llm)
        return self._stock_price_agent
    
    def _create_stock_price_tool(self) -> BaseTool:
        """표준 LangChain tool로 Stock Price Agent를 래핑합니다 (공식 패턴)"""
        
        @tool("call_stock_price_agent")
        def call_stock_price_agent(
            request: Annotated[str, "주가 데이터에 대한 분석 요청. 종목명, 티커, 기간, 분석 내용을 포함한 자연어 요청"]
        ) -> str:
            """
            Stock Price Agent를 호출하여 주가 데이터를 분석합니다.
            """
            try:
                print(f"📝 Stock Price Agent 요청: {request}")
                
                # 표준 LangGraph 방식으로 Sub-agent 호출
                stock_messages = [HumanMessage(content=request)]
                stock_state = MessagesState(
                    messages=stock_messages,
                    user_query=request,
                    extracted_info=None,
                    stock_data=None,
                    error=None,
                    metadata={"source": "supervisor_tool_call"}
                )
                
                # Stock Price Agent 실행 (표준 invoke)
                result_state = self.stock_price_agent.invoke(stock_state)
                
                # 결과 추출 (LangGraph 표준 방식)
                result_messages = result_state.get("messages", [])
                if result_messages:
                    # 마지막 메시지의 content 반환 (문자열)
                    final_response = result_messages[-1].content
                    return final_response
                else:
                    return "Stock Price Agent에서 응답을 받지 못했습니다."
                    
            except Exception as e:
                return f"Stock Price Agent 호출 중 오류 발생: {str(e)}"
        
        return call_stock_price_agent
    
    def invoke(self, state: MessagesState) -> Dict[str, Any]:
        """
        Supervisor Agent를 실행합니다 (표준 LangGraph Tool-calling Supervisor 패턴)
        
        Args:
            state: 현재 상태
            
        Returns:
            Dict: 업데이트된 상태
        """
        try:
            # 표준 LangGraph prebuilt create_react_agent 실행
            result = self.agent.invoke({"messages": state["messages"]})
            
            # 결과에서 메시지 추출 (표준 방식)
            new_messages = result.get("messages", [])
            
            # 메시지 상태 업데이트 (표준 방식)
            updated_state = state.copy()
            updated_state["messages"] = new_messages
            
            # 메타데이터 업데이트
            if updated_state["metadata"] is None:
                updated_state["metadata"] = {}
            updated_state["metadata"]["supervisor_processed"] = True
            updated_state["metadata"]["total_messages"] = len(new_messages)
            updated_state["metadata"]["pattern"] = "tool_calling_supervisor"
            
            return updated_state
            
        except Exception as e:
            # 오류 처리 (표준 방식)
            error_message = f"Supervisor Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 