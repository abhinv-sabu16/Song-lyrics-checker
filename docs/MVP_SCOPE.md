# MVP Scope

## What the MVP does
- Text lyric search: exact, partial and slightly misspelled phrases, ranked.
- Audio clip upload, local transcription (faster-whisper), then matching against the local lyrics index.
- Local SQLite storage, no mandatory paid API, no external transcription service.

## What the MVP will NOT do
- Identify arbitrary songs. It only matches songs present in the local lyrics database.
- Scrape lyrics from websites or bulk-download copyrighted lyrics.
- Audio fingerprinting (Chromaprint) or metadata lookup. Planned after Day 21.
- Guarantee transcription accuracy. Singing over music is inherently harder than speech.
- Return full lyrics. Results contain short matched excerpts only.
- Provide accounts, cloud sync, or remote access.

## Data policy
Only original, public-domain, or appropriately licensed lyrics go into the database.

## API contract (v0.2)
- `GET  /health` returns `{"status": "ok"}`
- `POST /api/search` takes `SearchRequest` and returns `SearchResponse`
- Validation errors return HTTP 422
- `similarity_score` is text similarity (0-100), never a probability of correctness