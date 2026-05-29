"""Import before routers so gettext context is available at module load time."""

from aiogram.utils.i18n import I18n

from bot.config.i18n import I18nConfigClass

_config = I18nConfigClass()
_i18n = I18n(
    path=str(_config.locales_path),
    default_locale=_config.default_lang,
    domain=_config.domain,
)
I18n.set_current(_i18n)
