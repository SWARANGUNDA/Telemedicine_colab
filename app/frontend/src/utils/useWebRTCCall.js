/**
 * useWebRTCCall.js — Production-Grade WebRTC Audio & HD Video Teleconsultation Hook for TeleMed.
 *
 * Manages the complete lifecycle of 1-to-1 Audio & HD Video calls between Patient and Doctor:
 * - Dual media streams (Microphone + HD Webcam / Camera)
 * - WebSocket signaling via /ws/call/{consultation_id} (CALL_REQUEST, ACCEPT, DECLINE, CANCEL, OFFER, ANSWER, ICE_CANDIDATE, MEDIA_TOGGLE, END)
 * - RTCPeerConnection with STUN/TURN configuration
 * - Track-level muting & camera pausing (retaining stream without renegotiation)
 * - Picture-in-Picture local preview & HD remote video binding
 * - Anti-stuck state guards & full cleanup on unmount / logout
 *
 * Security: Identity strictly verified server-side from JWT/session token. Zero media stored on server.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken, getWsBaseUrl } from '../api/client';

export const CALL_STATES = {
  IDLE: 'IDLE',
  CALLING: 'CALLING',
  RINGING: 'RINGING',
  ACCEPTED: 'ACCEPTED',
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  RECONNECTING: 'RECONNECTING',
  DECLINED: 'DECLINED',
  MISSED: 'MISSED',
  ENDED: 'ENDED',
  FAILED: 'FAILED',
};

export const CALL_TYPES = {
  AUDIO: 'AUDIO',
  VIDEO: 'VIDEO',
};

function getIceConfig() {
  const stunUrl = (typeof window !== 'undefined' && window.__TELEMED_STUN_URL__) || 'stun:stun.l.google.com:19302';
  const config = {
    iceServers: [
      { urls: stunUrl },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };
  if (typeof window !== 'undefined' && window.__TELEMED_TURN_URL__) {
    config.iceServers.push({
      urls: window.__TELEMED_TURN_URL__,
      username: window.__TELEMED_TURN_USER__ || '',
      credential: window.__TELEMED_TURN_CRED__ || '',
    });
  }
  return config;
}

export default function useWebRTCCall(consultationId, user) {
  const [callState, setCallState] = useState(CALL_STATES.IDLE);
  const [callType, setCallType] = useState(CALL_TYPES.AUDIO);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isRemoteVideoEnabled, setIsRemoteVideoEnabled] = useState(true);
  const [isRemoteMuted, setIsRemoteMuted] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [peerName, setPeerName] = useState('');
  const [peerRole, setPeerRole] = useState('');
  const [incomingCallInfo, setIncomingCallInfo] = useState(null);
  const [error, setError] = useState(null);
  const [facingMode, setFacingMode] = useState('user'); // 'user' | 'environment'

  const wsRef = useRef(null);
  const pcRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const durationTimerRef = useRef(null);
  const callStateRef = useRef(CALL_STATES.IDLE);
  const callTypeRef = useRef(CALL_TYPES.AUDIO);
  const stuckTimerRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const isCleaningUpRef = useRef(false);

  // Sync ref with call state
  const updateCallState = useCallback((newState) => {
    callStateRef.current = newState;
    setCallState(newState);
    if ([CALL_STATES.IDLE, CALL_STATES.CONNECTED, CALL_STATES.ENDED, CALL_STATES.FAILED, CALL_STATES.DECLINED, CALL_STATES.MISSED].includes(newState)) {
      if (stuckTimerRef.current) {
        clearTimeout(stuckTimerRef.current);
        stuckTimerRef.current = null;
      }
    }
  }, []);

  const updateCallType = useCallback((newType) => {
    callTypeRef.current = newType;
    setCallType(newType);
  }, []);

  // ── Duration Timer ───────────────────────────────────────────────────
  const startDurationTimer = useCallback(() => {
    setCallDuration(0);
    if (durationTimerRef.current) clearInterval(durationTimerRef.current);
    const startTime = Date.now();
    durationTimerRef.current = setInterval(() => {
      setCallDuration(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
  }, []);

  const stopDurationTimer = useCallback(() => {
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
  }, []);

  // ── Anti-Stuck Timer ─────────────────────────────────────────────────
  const setStuckTimeout = useCallback((timeoutMs = 30000) => {
    if (stuckTimerRef.current) clearTimeout(stuckTimerRef.current);
    stuckTimerRef.current = setTimeout(() => {
      const current = callStateRef.current;
      if ([CALL_STATES.CALLING, CALL_STATES.CONNECTING, CALL_STATES.ACCEPTED].includes(current)) {
        setError('Call could not be established. Please try again.');
        updateCallState(CALL_STATES.FAILED);
        cleanupCall();
      }
    }, timeoutMs);
  }, []);

  // ── Video Element Attachment Helper ──────────────────────────────────
  const bindLocalVideo = useCallback((element) => {
    localVideoRef.current = element;
    if (element && localStreamRef.current) {
      element.srcObject = localStreamRef.current;
      element.muted = true;
      element.play().catch(() => {});
    }
  }, []);

  const bindRemoteVideo = useCallback((element) => {
    remoteVideoRef.current = element;
    if (element && remoteStreamRef.current) {
      element.srcObject = remoteStreamRef.current;
      element.play().catch(() => {});
    }
  }, []);

  // ── Media Cleanup ────────────────────────────────────────────────────
  const stopLocalMedia = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => {
        try {
          track.stop();
          track.enabled = false;
        } catch (e) {}
      });
      localStreamRef.current = null;
    }
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = null;
    }
  }, []);

  const stopRemoteMedia = useCallback(() => {
    if (remoteStreamRef.current) {
      remoteStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      remoteStreamRef.current = null;
    }
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = null;
    }
  }, []);

  // ── RTCPeerConnection Cleanup ────────────────────────────────────────
  const closePeerConnection = useCallback(() => {
    if (pcRef.current) {
      pcRef.current.onicecandidate = null;
      pcRef.current.ontrack = null;
      pcRef.current.onconnectionstatechange = null;
      pcRef.current.oniceconnectionstatechange = null;
      pcRef.current.onnegotiationneeded = null;
      try { pcRef.current.close(); } catch (e) {}
      pcRef.current = null;
    }
  }, []);

  // ── Full Call Cleanup ────────────────────────────────────────────────
  const cleanupCall = useCallback(() => {
    if (isCleaningUpRef.current) return;
    isCleaningUpRef.current = true;

    stopDurationTimer();
    stopLocalMedia();
    stopRemoteMedia();
    closePeerConnection();

    if (stuckTimerRef.current) {
      clearTimeout(stuckTimerRef.current);
      stuckTimerRef.current = null;
    }

    setIsMuted(false);
    setIsVideoEnabled(true);
    setIsRemoteVideoEnabled(true);
    setIsRemoteMuted(false);
    setIncomingCallInfo(null);

    isCleaningUpRef.current = false;
  }, [stopDurationTimer, stopLocalMedia, stopRemoteMedia, closePeerConnection]);

  // ── Send Signaling Message ───────────────────────────────────────────
  const sendSignal = useCallback((payload) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }, []);

  // ── Create RTCPeerConnection ─────────────────────────────────────────
  const createPeerConnection = useCallback(() => {
    closePeerConnection();

    const pc = new RTCPeerConnection(getIceConfig());
    pcRef.current = pc;

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        sendSignal({
          event: 'ICE_CANDIDATE',
          candidate: event.candidate.toJSON(),
        });
      }
    };

    pc.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        const stream = event.streams[0];
        remoteStreamRef.current = stream;

        // Bind to remote video element if in video call or available
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = stream;
          remoteVideoRef.current.play().catch(() => {});
        }

        // Also bind to audio playback
        if (!remoteAudioRef.current) {
          remoteAudioRef.current = new Audio();
          remoteAudioRef.current.autoplay = true;
        }
        remoteAudioRef.current.srcObject = stream;
        remoteAudioRef.current.play().catch(() => {});
      }
    };

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState;
      if (state === 'connected') {
        updateCallState(CALL_STATES.CONNECTED);
        startDurationTimer();
      } else if (state === 'disconnected') {
        if (callStateRef.current === CALL_STATES.CONNECTED) {
          updateCallState(CALL_STATES.RECONNECTING);
          setStuckTimeout(10000);
        }
      } else if (state === 'failed') {
        setError('Connection lost. The call has ended.');
        updateCallState(CALL_STATES.FAILED);
        sendSignal({ event: 'CALL_END', reason: 'CONNECTION_FAILED' });
        cleanupCall();
      } else if (state === 'closed') {
        if (callStateRef.current !== CALL_STATES.ENDED && callStateRef.current !== CALL_STATES.IDLE) {
          updateCallState(CALL_STATES.ENDED);
          cleanupCall();
        }
      }
    };

    pc.oniceconnectionstatechange = () => {
      if (pc.iceConnectionState === 'failed') {
        if (callStateRef.current === CALL_STATES.CONNECTED || callStateRef.current === CALL_STATES.RECONNECTING) {
          pc.restartIce();
        }
      }
    };

    return pc;
  }, [closePeerConnection, sendSignal, updateCallState, startDurationTimer, setStuckTimeout, cleanupCall]);

  // ── Acquire Media (Audio & HD Video) ─────────────────────────────────
  const acquireMedia = useCallback(async (withVideo = false, facing = 'user') => {
    try {
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: withVideo ? {
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
          facingMode: facing,
          frameRate: { ideal: 30, min: 15 },
        } : false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      localStreamRef.current = stream;

      // Attach stream to local video element if video enabled
      if (withVideo && localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
        localVideoRef.current.muted = true;
        localVideoRef.current.play().catch(() => {});
      }

      setIsVideoEnabled(withVideo);
      setIsMuted(false);
      return stream;
    } catch (err) {
      if (withVideo && (err.name === 'NotAllowedError' || err.name === 'NotFoundError' || err.name === 'NotReadableError')) {
        // Graceful fallback to audio-only if camera fails
        try {
          const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
          localStreamRef.current = audioStream;
          setIsVideoEnabled(false);
          setIsMuted(false);
          setError('Camera was unavailable. Connected using audio only.');
          return audioStream;
        } catch (audioErr) {
          const msg = audioErr.name === 'NotAllowedError'
            ? 'Microphone access was denied. Please allow microphone access.'
            : 'Could not access microphone or camera.';
          setError(msg);
          throw new Error(msg);
        }
      }

      const msg = err.name === 'NotAllowedError'
        ? 'Media permission denied. Please allow microphone and camera access.'
        : err.name === 'NotFoundError'
          ? 'No microphone or camera device detected.'
          : 'Could not access audio/video devices.';
      setError(msg);
      throw new Error(msg);
    }
  }, []);

  // ── Handle Incoming Signaling Messages ───────────────────────────────
  const handleSignalingMessage = useCallback(async (data) => {
    const event = data.event;

    switch (event) {
      case 'CALL_CONNECTED':
        setPeerName(data.peer_name || '');
        break;

      case 'CALL_REQUEST': {
        if (callStateRef.current !== CALL_STATES.IDLE) {
          sendSignal({ event: 'CALL_DECLINE', reason: 'BUSY' });
          return;
        }
        const reqCallType = data.call_type || (data.with_video ? CALL_TYPES.VIDEO : CALL_TYPES.AUDIO);
        updateCallType(reqCallType);
        setIncomingCallInfo({
          senderName: data.sender_name || 'Unknown',
          senderRole: data.sender_role || 'UNKNOWN',
          consultationId: data.consultation_id,
          callType: reqCallType,
        });
        setPeerName(data.sender_name || 'Caller');
        setPeerRole(data.sender_role || '');
        updateCallState(CALL_STATES.RINGING);
        setStuckTimeout(45000);
        break;
      }

      case 'CALL_ACCEPT': {
        if (callStateRef.current !== CALL_STATES.CALLING) return;
        updateCallState(CALL_STATES.CONNECTING);
        setStuckTimeout(20000);
        try {
          const pc = createPeerConnection();
          const isVideo = callTypeRef.current === CALL_TYPES.VIDEO;
          const stream = localStreamRef.current || await acquireMedia(isVideo, facingMode);
          stream.getTracks().forEach(track => pc.addTrack(track, stream));

          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          sendSignal({
            event: 'CALL_OFFER',
            sdp: pc.localDescription.toJSON(),
            call_type: callTypeRef.current,
          });
        } catch (err) {
          setError('Failed to establish connection. Please try again.');
          updateCallState(CALL_STATES.FAILED);
          sendSignal({ event: 'CALL_END', reason: 'OFFER_FAILED' });
          cleanupCall();
        }
        break;
      }

      case 'CALL_DECLINE': {
        updateCallState(CALL_STATES.DECLINED);
        cleanupCall();
        break;
      }

      case 'CALL_CANCEL': {
        setIncomingCallInfo(null);
        updateCallState(CALL_STATES.ENDED);
        cleanupCall();
        break;
      }

      case 'CALL_OFFER': {
        if (callStateRef.current !== CALL_STATES.ACCEPTED && callStateRef.current !== CALL_STATES.CONNECTING) return;
        updateCallState(CALL_STATES.CONNECTING);
        setStuckTimeout(20000);
        try {
          const pc = createPeerConnection();
          const isVideo = (data.call_type === CALL_TYPES.VIDEO) || (callTypeRef.current === CALL_TYPES.VIDEO);
          updateCallType(isVideo ? CALL_TYPES.VIDEO : CALL_TYPES.AUDIO);

          const stream = localStreamRef.current || await acquireMedia(isVideo, facingMode);
          stream.getTracks().forEach(track => pc.addTrack(track, stream));

          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          sendSignal({
            event: 'CALL_ANSWER',
            sdp: pc.localDescription.toJSON(),
            call_type: callTypeRef.current,
          });
        } catch (err) {
          setError('Failed to connect call media.');
          updateCallState(CALL_STATES.FAILED);
          sendSignal({ event: 'CALL_END', reason: 'ANSWER_FAILED' });
          cleanupCall();
        }
        break;
      }

      case 'CALL_ANSWER': {
        if (!pcRef.current) return;
        try {
          await pcRef.current.setRemoteDescription(new RTCSessionDescription(data.sdp));
        } catch (err) {
          setError('Failed to finalize connection.');
          updateCallState(CALL_STATES.FAILED);
          cleanupCall();
        }
        break;
      }

      case 'ICE_CANDIDATE': {
        if (!pcRef.current) return;
        try {
          if (data.candidate) {
            await pcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
          }
        } catch (err) {
          // Non-fatal ICE candidate note
        }
        break;
      }

      case 'MEDIA_TOGGLE': {
        if (data.media_type === 'video') {
          setIsRemoteVideoEnabled(Boolean(data.enabled));
        } else if (data.media_type === 'audio') {
          setIsRemoteMuted(!Boolean(data.enabled));
        }
        break;
      }

      case 'CALL_END': {
        updateCallState(CALL_STATES.ENDED);
        cleanupCall();
        setIncomingCallInfo(null);
        break;
      }

      case 'CALL_ERROR': {
        const errorType = data.error_type;
        if (errorType === 'PEER_UNAVAILABLE') {
          setError('The other participant is not currently available.');
          if (callStateRef.current === CALL_STATES.CALLING) {
            updateCallState(CALL_STATES.FAILED);
            cleanupCall();
          }
        } else if (errorType === 'PEER_DISCONNECTED') {
          setError('The other participant disconnected.');
          updateCallState(CALL_STATES.FAILED);
          cleanupCall();
        } else {
          setError(data.message || 'An error occurred during the call.');
        }
        break;
      }

      case 'pong':
        break;

      default:
        break;
    }
  }, [sendSignal, updateCallState, updateCallType, createPeerConnection, acquireMedia, facingMode, cleanupCall, setStuckTimeout]);

  // ── WebSocket Signaling Connection ───────────────────────────────────
  useEffect(() => {
    const userId = user?.user_id || user?.id;
    if (!consultationId || !userId) return;

    const token = getAuthToken() || userId;
    if (!token) return;

    const wsUrl = `${getWsBaseUrl()}/ws/call/${consultationId}?token=${encodeURIComponent(token)}`;
    let ws;

    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;
    } catch (err) {
      return;
    }

    ws.onopen = () => {
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 20000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSignalingMessage(data);
      } catch (err) {
        // Ignored invalid signaling frame
      }
    };

    ws.onerror = () => {
      if ([CALL_STATES.CALLING, CALL_STATES.CONNECTING, CALL_STATES.CONNECTED].includes(callStateRef.current)) {
        setError('Signaling connection error. The teleconsultation may be interrupted.');
      }
    };

    ws.onclose = () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      if ([CALL_STATES.CALLING, CALL_STATES.RINGING, CALL_STATES.CONNECTING, CALL_STATES.CONNECTED, CALL_STATES.RECONNECTING].includes(callStateRef.current)) {
        updateCallState(CALL_STATES.ENDED);
        cleanupCall();
      }
    };

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      if (ws && ws.readyState !== WebSocket.CLOSED) {
        try { ws.close(); } catch (e) {}
      }
      wsRef.current = null;
    };
  }, [consultationId, user?.user_id]);

  // ── Tab Close / Beforeunload Cleanup ─────────────────────────────────
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (callStateRef.current !== CALL_STATES.IDLE && callStateRef.current !== CALL_STATES.ENDED) {
        sendSignal({ event: 'CALL_END', reason: 'TAB_CLOSED' });
        stopLocalMedia();
        stopRemoteMedia();
        closePeerConnection();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sendSignal, stopLocalMedia, stopRemoteMedia, closePeerConnection]);

  // ── Public Actions ───────────────────────────────────────────────────

  /** Start a call (Audio or HD Video) */
  const startCall = useCallback(async (type = CALL_TYPES.AUDIO) => {
    if (callStateRef.current !== CALL_STATES.IDLE) return;
    setError(null);
    updateCallType(type);

    try {
      const isVideo = type === CALL_TYPES.VIDEO;
      await acquireMedia(isVideo, facingMode);
      updateCallState(CALL_STATES.CALLING);
      setStuckTimeout(45000);

      const sent = sendSignal({
        event: 'CALL_REQUEST',
        call_type: type,
        with_video: isVideo,
      });

      if (!sent) {
        setError('Unable to reach signaling server. Please check your connection.');
        updateCallState(CALL_STATES.FAILED);
        cleanupCall();
      }
    } catch (err) {
      updateCallState(CALL_STATES.FAILED);
      cleanupCall();
    }
  }, [acquireMedia, facingMode, updateCallState, updateCallType, setStuckTimeout, sendSignal, cleanupCall]);

  /** Accept incoming call (with choice of audio/video) */
  const acceptCall = useCallback(async (withVideo = null) => {
    if (callStateRef.current !== CALL_STATES.RINGING) return;
    setError(null);

    const useVideo = withVideo !== null ? withVideo : (callTypeRef.current === CALL_TYPES.VIDEO);
    updateCallType(useVideo ? CALL_TYPES.VIDEO : CALL_TYPES.AUDIO);

    try {
      await acquireMedia(useVideo, facingMode);
      updateCallState(CALL_STATES.ACCEPTED);
      sendSignal({
        event: 'CALL_ACCEPT',
        call_type: useVideo ? CALL_TYPES.VIDEO : CALL_TYPES.AUDIO,
      });
      setStuckTimeout(20000);
    } catch (err) {
      updateCallState(CALL_STATES.FAILED);
      sendSignal({ event: 'CALL_DECLINE', reason: 'MEDIA_ERROR' });
      cleanupCall();
    }
  }, [acquireMedia, facingMode, updateCallState, updateCallType, sendSignal, setStuckTimeout, cleanupCall]);

  /** Decline incoming call */
  const declineCall = useCallback(() => {
    sendSignal({ event: 'CALL_DECLINE' });
    setIncomingCallInfo(null);
    updateCallState(CALL_STATES.IDLE);
    cleanupCall();
  }, [sendSignal, updateCallState, cleanupCall]);

  /** Cancel outgoing call before answer */
  const cancelCall = useCallback(() => {
    sendSignal({ event: 'CALL_CANCEL' });
    updateCallState(CALL_STATES.IDLE);
    cleanupCall();
  }, [sendSignal, updateCallState, cleanupCall]);

  /** End active call */
  const endCall = useCallback(() => {
    sendSignal({ event: 'CALL_END', reason: 'USER_HANGUP' });
    updateCallState(CALL_STATES.ENDED);
    cleanupCall();
  }, [sendSignal, updateCallState, cleanupCall]);

  /** Toggle microphone mute */
  const toggleMute = useCallback(() => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        const nextEnabled = !audioTrack.enabled;
        audioTrack.enabled = nextEnabled;
        setIsMuted(!nextEnabled);
        sendSignal({
          event: 'MEDIA_TOGGLE',
          media_type: 'audio',
          enabled: nextEnabled,
        });
      }
    }
  }, [sendSignal]);

  /** Toggle camera video on/off */
  const toggleVideo = useCallback(async () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        const nextEnabled = !videoTrack.enabled;
        videoTrack.enabled = nextEnabled;
        setIsVideoEnabled(nextEnabled);
        sendSignal({
          event: 'MEDIA_TOGGLE',
          media_type: 'video',
          enabled: nextEnabled,
        });
      } else {
        // Video track was not originally acquired — add camera to stream
        try {
          const videoStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode },
          });
          const newVideoTrack = videoStream.getVideoTracks()[0];
          localStreamRef.current.addTrack(newVideoTrack);
          if (pcRef.current) {
            pcRef.current.addTrack(newVideoTrack, localStreamRef.current);
          }
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = localStreamRef.current;
            localVideoRef.current.play().catch(() => {});
          }
          setIsVideoEnabled(true);
          updateCallType(CALL_TYPES.VIDEO);
          sendSignal({
            event: 'MEDIA_TOGGLE',
            media_type: 'video',
            enabled: true,
          });
        } catch (e) {
          setError('Could not enable camera device.');
        }
      }
    }
  }, [facingMode, sendSignal, updateCallType]);

  /** Switch camera (front / back) */
  const switchCamera = useCallback(async () => {
    const nextFacing = facingMode === 'user' ? 'environment' : 'user';
    setFacingMode(nextFacing);

    if (localStreamRef.current && isVideoEnabled) {
      const oldVideoTrack = localStreamRef.current.getVideoTracks()[0];
      if (oldVideoTrack) {
        oldVideoTrack.stop();
        localStreamRef.current.removeTrack(oldVideoTrack);
      }
      try {
        const newStream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: nextFacing },
        });
        const newTrack = newStream.getVideoTracks()[0];
        localStreamRef.current.addTrack(newTrack);

        if (pcRef.current) {
          const sender = pcRef.current.getSenders().find(s => s.track && s.track.kind === 'video');
          if (sender) {
            sender.replaceTrack(newTrack);
          } else {
            pcRef.current.addTrack(newTrack, localStreamRef.current);
          }
        }

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = localStreamRef.current;
          localVideoRef.current.play().catch(() => {});
        }
      } catch (err) {
        // Camera switch failed silently
      }
    }
  }, [facingMode, isVideoEnabled]);

  const clearError = useCallback(() => setError(null), []);

  const resetToIdle = useCallback(() => {
    cleanupCall();
    setError(null);
    setIncomingCallInfo(null);
    updateCallState(CALL_STATES.IDLE);
  }, [cleanupCall, updateCallState]);

  /** Full teardown for logout */
  const fullCleanup = useCallback(() => {
    if (callStateRef.current !== CALL_STATES.IDLE && callStateRef.current !== CALL_STATES.ENDED) {
      sendSignal({ event: 'CALL_END', reason: 'LOGOUT' });
    }
    cleanupCall();
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      try { wsRef.current.close(); } catch (e) {}
      wsRef.current = null;
    }
    setError(null);
    setIncomingCallInfo(null);
    setPeerName('');
    setPeerRole('');
    setCallDuration(0);
    setIsMuted(false);
    setIsVideoEnabled(true);
    setIsRemoteVideoEnabled(true);
    setIsRemoteMuted(false);
    updateCallState(CALL_STATES.IDLE);
  }, [sendSignal, cleanupCall, updateCallState]);

  return {
    // States
    callState,
    callType,
    isMuted,
    isVideoEnabled,
    isRemoteVideoEnabled,
    isRemoteMuted,
    callDuration,
    peerName,
    peerRole,
    incomingCallInfo,
    error,
    facingMode,

    // Refs / Binders
    bindLocalVideo,
    bindRemoteVideo,

    // Actions
    startCall,
    acceptCall,
    declineCall,
    cancelCall,
    endCall,
    toggleMute,
    toggleVideo,
    switchCamera,
    clearError,
    resetToIdle,
    fullCleanup,
  };
}
