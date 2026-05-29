from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path


def _configure_pythonpath() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for path in (root, src):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def main() -> None:
    _configure_pythonpath()
    logging.basicConfig(level=logging.INFO)
    from bot.config.bot import BotConfigClass
    from bot.core.app import BotApplication
    from bot.core.container import AppContainer

    container = AppContainer.build(BotConfigClass())  # type: ignore[call-arg]
    app = BotApplication(container)
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
