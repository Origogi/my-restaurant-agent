# restaurant-agent

Streamlit UI 위에서 동작하는 OpenAI Agents SDK 기반 레스토랑 어시스턴트 샘플입니다.

현재 구조는 매 사용자 턴마다 `Triage Agent`가 먼저 요청을 분류하고, 필요하면 전문 서브 에이전트로 handoff 하는 방식입니다.

## Agents

- `Triage Agent`: 사용자의 의도를 파악하고 적절한 서브 에이전트로 라우팅
- `Menu Agent`: 메뉴, 재료, 추천, 알레르기/식이 관련 질문 처리
- `Order Agent`: 주문 접수, 수량/옵션 확인, 주문 요약 처리
- `Reservation Agent`: 예약 생성, 변경, 취소, 인원/시간 관련 질문 처리

## Handoff Diagram

```text
User
  |
  v
Triage Agent
  |---> Menu Agent
  |---> Order Agent
  `---> Reservation Agent
```

핵심 동작:

- 모든 새 사용자 메시지는 항상 `Triage Agent`부터 시작합니다.
- 한 턴 안에서는 specialist agent로 handoff 될 수 있습니다.
- 다음 사용자 턴이 시작되면 다시 `Triage Agent`가 분류를 수행합니다.

## Project Structure

```text
.
├── main.py
├── models.py
├── my_agents
│   ├── __init__.py
│   ├── triage_agent.py
│   ├── menu_agent.py
│   ├── order_agent.py
│   └── reservation_agent.py
├── pyproject.toml
└── README.md
```

## Setup

1. 환경변수 파일 생성

```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

2. 의존성 설치

```bash
uv sync
```

3. 앱 실행

```bash
streamlit run main.py
```

## Example Prompts

- `오늘 저녁 7시에 4명 예약하고 싶어요`
- `채식 메뉴 추천해줘`
- `버거 두 개랑 콜라 하나 주문할게요`
- `견과류 들어간 메뉴가 있나요?`

## Notes

- handoff 발생 시 UI에 `Transferred to ...` 메시지가 표시됩니다.
- 이전 handoff 메시지는 세션 히스토리에서도 다시 렌더링됩니다.
- 현재 예제는 실제 주문/예약 저장소 없이 agent 라우팅과 응답 흐름에 집중한 샘플입니다.
