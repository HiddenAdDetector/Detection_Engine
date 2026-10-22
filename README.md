# AdSentinel Detection Engine

행정안전부·NIA **공공 웹사이트 불법광고 탐지 도구 개발 공모전** 출품작 AdSentinel의 탐지 엔진입니다. 크롤러가 수집한 DOM 요소 JSON을 받아 우회·은닉 기법을 탐지하고, 공모전 규격의 `result.json`을 생성합니다.

이 저장소는 A 파트만 담당합니다. 크롤링과 GUI는 포함하지 않으며 브라우저 없이 샘플 JSON으로 독립 실행할 수 있습니다.

## 주요 기능

- `JAMO`: `ㅋㅏㅈㅣㄴㅗ`처럼 분해된 한글 자모를 복원해 검사
- `HOMOGLYPH`: 전각 문자, 키릴 문자, 숫자·기호 유사 문자를 정규화해 검사
- `TRANSPARENT`: 투명도, 투명 글자색, 배경과 낮은 명암비 등 탐지
- `OFFSCREEN`: 작은 글자, 화면 밖 배치, `display:none`, clipping 등 탐지
- 예방·신고·단속 안내와 접근성용 숨김 텍스트의 오탐 억제
- 선택적 Google Gemini 문맥 판정, 숨김형 규칙 양성 재검토, 실패 시 규칙 엔진 자동 폴백
- 공모전 30분 상한보다 짧은 기본 제한시간과 취소 파일을 이용한 부분 결과 저장
- 저장 후 결과 스키마·중복·UTF-8 BOM 재검증과 모호한 위치 선택자 차단
- PyInstaller 단일 실행 파일 배포 지원

은닉 상태만으로는 위반으로 판정하지 않습니다. 규칙 엔진은 불법광고 키워드가 함께 확인된 경우에만 위반으로 판단합니다. 사전에 없는 의심 후보와 숨김형 규칙 양성 중 오탐 가능성이 있는 결과는 설정된 경우 Gemini가 문맥을 재검토하며, 별도 오탐 신호가 없는 명확한 자모·닮은꼴 문자 결과는 규칙 판정을 유지합니다.

현재 도구 버전은 **0.5.0**입니다.

## 환경

- Windows 11
- Python 3.13
- 필수 런타임 패키지: `python-dotenv`
- AI 기능 사용 시: `google-genai`
- 테스트: `pytest`
- exe 빌드: `pyinstaller`

개발 의존성 설치 예시:

```powershell
python -m pip install pytest python-dotenv google-genai pyinstaller
```

Gemini를 사용하지 않는 환경에서도 탐지와 `result.json` 생성은 정상 동작합니다.

## 빠른 실행

저장소 루트에서 다음 명령을 실행합니다.

```powershell
python detector_cli.py `
  --input samples\b_elements_sample.json `
  --out-dir output `
  --no-ai
```

생성 파일:

```text
output/
├── result.json
└── detect_log.jsonl
```

stdout은 사람이 읽는 문장이 아니라 UTF-8 JSON Lines로 출력됩니다.

```json
{"type":"progress","state":"rule","done":1,"total":2}
{"type":"progress","state":"done","done":2,"total":2}
{"type":"result","path":"C:\\work\\output\\result.json","findings":2,"cancelled":false,"ai_used":false}
```

## CLI 사용법

```text
python detector_cli.py --input <elements.json> [--out-dir <폴더>] [옵션]
```

PyInstaller 빌드 후에도 같은 옵션을 사용합니다.

```text
detector_cli.exe --input <elements.json> --out-dir <폴더>
```

| 옵션 | 설명 |
|---|---|
| `--input` | 입력 JSON 경로. 필수 |
| `--out-dir` | 결과 폴더. 생략하면 스크립트 또는 exe가 있는 폴더 |
| `--entry-url` | 입력 JSON의 `entry_url`을 덮어씀 |
| `--started-at` | ISO 8601 탐지 시작 시각을 덮어씀 |
| `--deadline-sec N` | N초 뒤 취소하고 그때까지의 결과를 저장. 기본값 1700초 |
| `--cancel-file PATH` | 파일이 생성되면 취소하고 부분 결과를 저장 |
| `--no-ai` | Gemini를 호출하지 않고 규칙 엔진만 사용 |
| `--topic` | 결과의 topic 지정. 기본값은 기존 `TOPIC` 상수 |
| `--tool-version` | 결과에 기록할 도구 버전 |

종료 코드는 정상·취소·제한시간 만료 시 `0`, 입력 오류 시 `2`, 예기치 못한 오류 시 `1`입니다. 입력 오류가 발생해도 가능한 경우 `findings: []`인 결과 파일을 생성합니다.

Java/Spring Boot 연동과 취소 파일 사용법은 [CLI 연동 계약](detector/CLI_CONTRACT.md)을 참고하세요.

## 입력 JSON

권장 최상위 구조:

```json
{
  "entry_url": "https://www.example.go.kr/",
  "started_at": "2026-10-22T09:00:00+09:00",
  "elements": [
    {
      "url": "https://www.example.go.kr/page",
      "location": "main > span.banner",
      "framePath": "https://www.example.go.kr/widget",
      "text": "ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ",
      "context": "배너 주변 문맥",
      "style": {
        "opacity": "0",
        "fontSize": "14px",
        "display": "block"
      },
      "bbox": {"x": 10, "y": 20, "width": 150, "height": 20}
    }
  ]
}
```

최상위 배열도 허용합니다. `frame_path`와 `framePath`를 모두 지원하며 문자열 하나는 한 항목짜리 목록으로 처리합니다. 알 수 없는 필드는 무시하고 누락된 `style`, `bbox`, `context`는 빈 값으로 처리합니다. 자세한 DOM 수집 규격은 [Element 스타일 계약](detector/STYLE_KEYS.md)에 있습니다.

## result.json

최상위에는 `meta`와 `findings`만 기록합니다. 탐지 결과가 없어도 `findings: []`를 포함합니다.

각 finding은 다음 여섯 필드만 가집니다.

```json
{
  "id": "f_001",
  "url": "https://www.example.go.kr/page",
  "is_violation": true,
  "location": "iframe[src=\"https://www.example.go.kr/widget\"] >>> main > span.banner",
  "evidence_text": "ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ",
  "technique": "JAMO"
}
```

한 요소에서 여러 기법이 확인되면 기법별 finding으로 분리됩니다. `technique` 값은 `JAMO`, `HOMOGLYPH`, `TRANSPARENT`, `OFFSCREEN` 중 하나입니다. UTF-8 BOM 없이 저장되며 원본 증거 문구는 정규화하지 않고 유지합니다.

공통 태그명만 사용한 `div`, `span`, `p`, `a` 등의 모호한 `location`은 여러 요소를 가리켜 오답이 될 가능성이 높으므로 입력 단계에서 제외합니다. 결과 저장 후에는 파일을 다시 읽어 필수 필드, 허용 기법, 중복 ID·검출, UTF-8 BOM 여부를 검증합니다.

## Gemini 설정

프로젝트 루트에서 `.env.example`을 `.env`로 복사하고 필요한 값을 입력합니다.

```powershell
Copy-Item .env.example .env
```

```dotenv
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT_SEC=20
GEMINI_BATCH_SIZE=20
GEMINI_MAX_CALLS=30
GEMINI_MIN_CONFIDENCE=0.7
GEMINI_TOTAL_BUDGET_SEC=120
```

`.env`는 스크립트 또는 exe 옆에서 읽기 때문에 키 교체를 위해 다시 빌드할 필요가 없습니다. 키가 없거나 네트워크·API 호출이 실패하면 규칙 판정으로 자동 폴백합니다. API 키는 stdout, stderr, 예외 메시지, `detect_log.jsonl`에 기록하지 않습니다. 동일 텍스트라도 주변 문맥이나 탐지 기법이 다르면 별도 후보로 판정하며, 숨김형 규칙 양성처럼 오탐 가능성이 있는 결과는 AI가 높은 신뢰도로 광고가 아니라고 판단할 때 제외할 수 있습니다.

자세한 내용은 [Gemini 설정 안내](detector/AI_SETUP.md)를 참고하세요.

## 취소와 제한시간

기본 제한시간은 공모전의 30분 상한보다 짧은 1700초입니다. 더 짧은 시간 제한을 지정하려면 다음처럼 실행합니다.

```powershell
python detector_cli.py --input elements.json --out-dir output --deadline-sec 1500
```

외부 프로그램에서 안전하게 중지하려면 `--cancel-file`을 전달하고, 중지 시 해당 파일을 생성합니다.

```powershell
python detector_cli.py `
  --input elements.json `
  --out-dir output `
  --cancel-file output\cancel.request
```

CLI는 파일 존재 여부를 0.5초 간격으로 확인합니다. 취소는 정상 종료 코드 `0`으로 처리되고 확보된 탐지 결과가 저장됩니다. 실행 전 이전 취소 파일은 제거해야 합니다.

## 테스트

전체 테스트는 네트워크 호출 없이 실행됩니다.

```powershell
python -m pytest -q
```

현재 규칙 엔진, AI mock, 규칙 양성 재검토, 문맥별 후보 분리, 모호한 위치 차단, 엄격한 결과 스키마 및 실제 CLI 서브프로세스 테스트를 포함해 **90개 테스트**가 통과합니다.

## exe 빌드

PyInstaller를 설치한 뒤 다음 스크립트를 실행합니다.

```powershell
.\build_cli.bat
```

성공하면 다음 파일이 생성됩니다.

```text
dist\detector_cli.exe
```

빌드 후 확인 예시:

```powershell
.\dist\detector_cli.exe --help
.\dist\detector_cli.exe `
  --input samples\b_elements_sample.json `
  --out-dir output `
  --no-ai
```

`.env`는 `detector_cli.exe`와 같은 폴더에 배치합니다.

## 프로젝트 구조

```text
Detection_Engine/
├── detector/
│   ├── ai_judge.py       # Gemini 후보 판정과 안전한 폴백
│   ├── engine.py         # 규칙 및 AI 판정 조합
│   ├── hidden.py         # TRANSPARENT/OFFSCREEN 판정
│   ├── homoglyph.py      # 유사문자 정규화
│   ├── jamo.py           # 호환 자모 재조합
│   ├── keywords.py       # 키워드와 오탐 억제 문맥
│   ├── models.py         # Element/Verdict 데이터 계약
│   └── result_writer.py  # result.json 생성
├── samples/              # 브라우저 없는 실행용 입력 예시
├── tests/                # pytest 테스트
├── detector_cli.py       # 서브프로세스 CLI 진입점
├── build_cli.bat         # Windows onefile 빌드
└── .env.example          # Gemini 설정 예시
```

## 공개 Python 인터페이스

```python
from detector.engine import detect
from detector.result_writer import write_result

verdicts = detect(elements, use_ai=True, cancel_event=cancel_event)
result_path = write_result(
    entry_url=entry_url,
    started_at=started_at,
    finished_at=finished_at,
    verdicts=verdicts,
    out_dir=output_dir,
    tool_version="0.5.0",
)
```

- `detect(elements, use_ai=True, cancel_event=None, on_progress=None)`
- `write_result(entry_url, started_at, finished_at, verdicts, out_dir, tool_version, topic)`
