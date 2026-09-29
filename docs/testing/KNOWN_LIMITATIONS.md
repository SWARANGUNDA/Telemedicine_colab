# TeleMed AI — Known System Limitations & Future Work

## 1. File Upload Processing
- PDF OCR parsing relies on system Tesseract installation. Scanned reports with heavy background noise may require manual feature review.

## 2. PWA Offline Caching
- Offline caching is strictly limited to static application bundle assets (`sw.js`). Dynamic risk prediction calls (`/api/v1/predict/v3`) require active internet connectivity.

## 3. WebRTC Teleconsultation
- WebRTC video call sessions use local browser peer connections. Production multi-party consultations require TURN/STUN server configuration.
