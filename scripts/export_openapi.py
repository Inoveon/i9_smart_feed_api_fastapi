from pathlib import Path
import json
from fastapi.openapi.utils import get_openapi
from app.main import app


def main() -> None:
    out = Path('docs/api')
    out.mkdir(parents=True, exist_ok=True)
    openapi = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    (out / 'openapi.json').write_text(json.dumps(openapi, indent=2), encoding='utf-8')
    print('✓ OpenAPI gerado em docs/api/openapi.json')


if __name__ == '__main__':
    main()

