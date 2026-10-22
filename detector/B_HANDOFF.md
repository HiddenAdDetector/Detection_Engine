# B 파트 인계 사항

## 25분 전체 하드 컷오프

공모전의 30분 타임아웃보다 5분 일찍 종료할 수 있도록, B는 **크롤링 시작 시점**에 하나의 `threading.Event`와 25분 타이머를 생성한다. 크롤링 루프도 이 이벤트를 확인하고, 같은 이벤트를 A의 `detect()`에 전달한다.

```python
from threading import Event, Timer

cancel_event = Event()
hard_cutoff = Timer(25 * 60, cancel_event.set)
hard_cutoff.daemon = True
hard_cutoff.start()

try:
    # crawler.collect(..., cancel_event=cancel_event)
    verdicts = detect(
        elements,
        use_ai=True,
        cancel_event=cancel_event,
        on_progress=on_progress,
    )
finally:
    hard_cutoff.cancel()

# 취소·타임아웃이어도 확보한 verdicts로 write_result(...)를 호출한다.
```

A의 AI 단계는 별도로 `GEMINI_TOTAL_BUDGET_SEC` 기본 120초를 적용한다. 이 예산이나 `cancel_event` 중 하나가 먼저 만료되면 진행 중 Gemini 호출을 기다리지 않고 규칙 결과로 폴백한다.

## PyInstaller 첫 빌드 확인

B의 첫 Windows 11 빌드에서 아래를 반드시 확인한다.

1. exe 시작 시 `google.genai`와 `dotenv` import가 성공하는지 확인한다.
2. `google-genai`, `python-dotenv`가 PyInstaller 분석/수집 대상에 포함됐는지 확인한다.
3. exe와 같은 폴더의 `.env`에서 `GEMINI_API_KEY`와 `GEMINI_MODEL`을 읽는지 확인한다.
4. 키가 없을 때도 예외 없이 규칙 탐지와 `result.json` 생성이 완료되는지 확인한다.
5. 테스트 키를 넣었을 때 재빌드 없이 AI 호출이 활성화되는지 확인한다.
6. 중지 버튼이 같은 `cancel_event`를 set하고, 진행 중 AI 호출을 기다리지 않고 결과 저장 단계로 이동하는지 확인한다.

스타일·iframe 입력 계약은 [STYLE_KEYS.md](STYLE_KEYS.md)를 함께 전달한다.
