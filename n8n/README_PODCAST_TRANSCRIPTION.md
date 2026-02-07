# Podcast Transcription with Caching - Changes Log

## Date: 2026-02-07

### New Workflow: API - Transcribe Podcast v2
**File:** `API_-_Transcribe_Podcast_v2.json`
**Webhook URL:** `https://n8n.aimediaflow.net/webhook/transcribe-podcast`
**Status:** ✅ Active

#### Features Added:
1. **Intelligent Caching System**
   - Uses n8n Data Table `podcast_transcripts` to cache transcriptions
   - Checks cache before transcribing (saves 3-5 minutes per cached podcast)
   - Automatically saves new transcriptions to cache

2. **Dual-Path Processing**
   - **Path 1 (Cached):** Check Cache → Get From Cache → Return Cached → Respond
   - **Path 2 (New):** If Not In Cache → Download → Compress → Whisper → Save → Respond

3. **Audio Compression**
   - Integrates with FFmpeg service (`http://ffmpeg-audio-compressor:3000/compress`)
   - Compresses large audio files (>20MB) before transcription
   - Reduces transcription time from 6-7 minutes to 2-3 minutes

4. **HTTP Caching Headers**
   - Disabled browser caching with headers:
     - `Cache-Control: no-cache, no-store, must-revalidate`
     - `Pragma: no-cache`
     - `Expires: 0`
   - Ensures fresh data on every request

5. **Webhook TypeVersion Fix**
   - Changed from typeVersion 2 to typeVersion 1
   - Fixed query parameter handling issue
   - Now correctly receives `?audioUrl=...&podcastId=...`

#### Data Table Schema: `podcast_transcripts`
```
- id (auto-increment)
- audio_url (string) - Primary lookup key
- transcript_text (string) - Full transcript
- segments (string) - JSON with timestamps
- file_size_mb (number) - Original file size
- createdAt, updatedAt (timestamps)
```

#### Technical Details:
- **Nodes:** 13 total
  - Webhook (typeVersion 1)
  - Get Audio URL (Code)
  - Check Cache (DataTable rowExists)
  - If Not In Cache (DataTable rowNotExists)
  - Get From Cache (DataTable get)
  - Return Cached (Code)
  - Download Audio (HTTP Request)
  - Check File Size (Code)
  - Compress Audio (HTTP Request)
  - Send to Whisper (HTTP Request)
  - Format Response (Code)
  - Save to Cache (DataTable upsert)
  - Respond to Webhook

- **Performance:**
  - Cached response: ~300ms
  - New transcription: 2-7 minutes (depending on file size and compression)

#### Frontend Changes (`index.html`):
1. Added confirmation dialog before transcription
2. Fixed duplicate `podcastTranscripts` variable declaration
3. Added visual indicators for cached transcripts (prepared, not yet active)
4. Cache availability check endpoint prepared (not yet active)

### Changes Made to Existing Code:
1. **Webhook Node:**
   - Changed `typeVersion` from 2 to 1 (critical fix for query params)
   - Added `onError: "continueRegularOutput"`

2. **Response Headers:**
   - Added anti-caching headers to prevent browser cache issues

3. **Data Flow:**
   - Split into two parallel paths from "Get Audio URL"
   - Both paths converge at "Respond to Webhook"

### Known Issues:
1. **Check Transcripts Workflow** (DxnyDCVptGINm9tP) - Created but not active
   - Intended to check multiple podcasts for cached transcripts
   - Frontend prepared to use it but endpoint not working yet
   - Workaround: Always ask for confirmation before transcription

### Migration Notes:
- Old workflow "API - Transcribe Podcast" (T4amaL9X8Z9vZG7Q) is archived
- No data migration needed - cache will build up organically
- FFmpeg compressor service must be running: `docker ps | grep ffmpeg`

### Testing:
```bash
# Test with new podcast (will transcribe)
curl "https://n8n.aimediaflow.net/webhook/transcribe-podcast?audioUrl=http://example.com/podcast.mp3&podcastId=123"

# Test again (will use cache)
curl "https://n8n.aimediaflow.net/webhook/transcribe-podcast?audioUrl=http://example.com/podcast.mp3&podcastId=123"
```

### Rollback Plan:
If needed, reactivate old workflow T4amaL9X8Z9vZG7Q and change frontend endpoint back to original URL.
