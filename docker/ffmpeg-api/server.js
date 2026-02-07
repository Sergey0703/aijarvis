const express = require('express');
const multer = require('multer');
const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');
const path = require('path');

const app = express();
const upload = multer({ dest: '/tmp/uploads/' });

// Compress audio: mono, 16kHz, 32kbps
app.post('/compress', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No audio file provided' });
  }

  const inputPath = req.file.path;
  const outputPath = `/tmp/compressed-${Date.now()}.mp3`;

  try {
    await new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .audioChannels(1)           // Mono
        .audioFrequency(16000)      // 16kHz (optimal for speech)
        .audioBitrate('32k')        // 32kbps
        .audioCodec('libmp3lame')   // MP3 codec
        .format('mp3')
        .on('end', resolve)
        .on('error', reject)
        .save(outputPath);
    });

    const originalSize = fs.statSync(inputPath).size;
    const compressedSize = fs.statSync(outputPath).size;
    const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(1);

    console.log(`Compressed: ${(originalSize / 1024 / 1024).toFixed(2)} MB → ${(compressedSize / 1024 / 1024).toFixed(2)} MB (${compressionRatio}% reduction)`);

    // Send compressed file
    res.sendFile(outputPath, (err) => {
      // Cleanup
      fs.unlinkSync(inputPath);
      fs.unlinkSync(outputPath);
      if (err) console.error('Error sending file:', err);
    });

  } catch (error) {
    console.error('FFmpeg error:', error);
    fs.unlinkSync(inputPath);
    res.status(500).json({ error: 'Compression failed', details: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'ffmpeg-audio-compressor' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`FFmpeg Audio Compressor API listening on port ${PORT}`);
});
