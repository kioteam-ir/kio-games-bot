from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path


def _configure_pythonpath() -> None:
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def main() -> None:
    _configure_pythonpath()
    logging.basicConfig(level=logging.INFO)
    import bot.i18n_bootstrap  # noqa: F401
    from bot.config.bot import BotConfigClass
    from bot.core.app import BotApplication
    from bot.core.container import AppContainer

    container = AppContainer.build(BotConfigClass())  # type: ignore[call-arg]
    app = BotApplication(container)
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
