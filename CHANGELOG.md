# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-11-02

### Added
- **Interactive Start Game Inline Button:** Added "🎮 شروع بازی" button on `/start` using Telegram's `switch_inline_query_chosen_chat` to switch directly into private chats or groups with the bot username prefilled.
- **Multilingual Support for Start Prompt & Button:** Localized the welcome message and start button across all 12 supported languages (`fa`, `en`, `ar`, `tr`, `ru`, `de`, `fr`, `he`, `zh`, `ku`, `ps`, `hi`).
- **Comprehensive Sponsor Join Guidance:** Localized sponsor join alert popups in all 12 languages instructing users to re-click the button after joining sponsor channels.
- **Admin Management Commands:** Added `/add_sps` command with automatic channel resolution and admin permission verification for easier sponsor channel management.

### Fixed
- **Real-time Sponsor Verification & Dynamic Cache Invalidation:** Removed negative caching and included active sponsor signatures in user cache keys so adding/removing sponsors or joining/leaving takes effect instantly.
- **In-Game Sponsor Membership Enforcement:** Enforced sponsor membership checks during gameplay (cell moves) to prevent non-members from continuing matches.
- **Channel ID Auto-Healing:** Added automatic resolution for channels experiencing `chat not found` errors due to invalid ID formatting.
- **Rate Limit Adjustments:** Relaxed callback and inline query rate limits to eliminate false-positive throttling during game creation and joining.

## [0.4.1] - 2026-06-12

### Added
- Added `httpx2` dependency to `pyproject.toml`.

## [0.4.0] - 2026-06-12

### Changed
- Code formatting and style cleanup across the repository using Ruff.

## [0.3.1] - 2026-06-12

### Changed
- Formatting adjustments for Python source files.

## [0.3.0] - 2026-06-12

### Fixed
- Pointed migration tests at a tracked fixture for CI compatibility.

## [0.2.0-prod] - 2026-05-29

### Added
- Initial Clean Architecture bot refactor with aiogram 3.
- Multilingual support across 9 initial languages with language switcher.
- Idempotency, rate limiting, and caching layers.
