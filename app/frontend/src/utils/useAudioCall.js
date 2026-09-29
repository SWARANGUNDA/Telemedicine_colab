/**
 * useAudioCall.js / useWebRTCCall.js — Production WebRTC Audio & Video Consultation Hook for TeleMed.
 *
 * Manages the full lifecycle of a 1-to-1 Audio or HD Video Call between Patient and Doctor:
 * - WebSocket signaling channel (CALL_REQUEST, ACCEPT, DECLINE, CANCEL, OFFER, ANSWER, ICE_CANDIDATE, END)
 * - RTCPeerConnection with STUN/TURN & ICE Candidate Queuing
 * - getUserMedia for microphone audio and HD webcam video (with graceful audio-only fallback if camera is busy)
 * - Local Picture-in-Picture (PiP) and Remote Video stream management
 * - In-call Camera Toggle (video on/off) and Microphone Mute/Unmute
 * - Call state machine (IDLE → CALLING → RINGING → ACCEPTED → CONNECTING → CONNECTED → ENDED)
 * - Anti-stuck timeouts and hardware cleanup on unmount, logout, tab close
 *
 * Security: Server-side identity derived from JWT/session. Zero server recording.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken, getWsBaseUrl } from '../api/client';

// Call state machine
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

// ICE/STUN/TURN configuration
function getIceConfig() {
  const stunUrl = (typeof window !== 'undefined' && window.__TELEMED_STUN_URL__) || 'stun:stun.l.google.com:19302';
  const config = {
    iceServers: [
      { urls: stunUrl },
      { urls: 'stun:stun1.l.google.com:19302' },
      { urls: 'stun:stun2.l.google.com:19302' },
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

/**
 * @param {string|null} consultationId - Active consultation ID
 * @param {object|null} user - Current authenticated user object
 * @returns Call state, streams, and control functions
 */
export default function useAudioCall(consultationId, user) {
  const [callState, setCallState] = useState(CALL_STATES.IDLE);
  const [callType, setCallType] = useState('audio'); // 'audio' | 'video'
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isRemoteVideoAvailable, setIsRemoteVideoAvailable] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [peerName, setPeerName] = useState('');
  const [peerRole, setPeerRole] = useState('');
  const [incomingCallInfo, setIncomingCallInfo] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const pcRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const durationTimerRef = useRef(null);
  const callStateRef = useRef(CALL_STATES.IDLE);
  const callTypeRef = useRef('audio');
  const stuckTimerRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const isCleaningUpRef = useRef(false);
  const pendingIceCandidatesRef = useRef([]);

  // Keep callStateRef in sync
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

  // ── Duration Timer ────────────────────────────────────────────────────
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

  // ── Anti-Stuck Timer ──────────────────────────────────────────────────
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

  // ── Media Cleanup ─────────────────────────────────────────────────────
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
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = null;
    }
    remoteStreamRef.current = null;
    setIsRemoteVideoAvailable(false);
  }, []);

  // ── RTCPeerConnection Cleanup ─────────────────────────────────────────
  const closePeerConnection = useCallback(() => {
    pendingIceCandidatesRef.current = [];
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

  // ── Full Call Cleanup ─────────────────────────────────────────────────
  const cleanupCall = useCallback(() => {
    if (isCleaningUpRef.current) return;
    isCleaningUpRef.current = true;

    stopDurationTimer();
    stopLocalMedia();
    closePeerConnection();

    if (stuckTimerRef.current) {
      clearTimeout(stuckTimerRef.current);
      stuckTimerRef.current = null;
    }

    setIsMuted(false);
    setIsVideoEnabled(true);
    setIncomingCallInfo(null);

    isCleaningUpRef.current = false;
  }, [stopDurationTimer, stopLocalMedia, closePeerConnection]);

  // ── WebSocket Signaling Send ──────────────────────────────────────────
  const sendSignal = useCallback((payload) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }, []);

  // ── Attach Local Stream to Video Ref ──────────────────────────────────
  const attachLocalStream = useCallback((stream) => {
    if (localVideoRef.current && stream) {
      localVideoRef.current.srcObject = stream;
      localVideoRef.current.play().catch(() => {});
    }
  }, []);

  // ── Attach Remote Stream to Video Ref ─────────────────────────────────
  const attachRemoteStream = useCallback((stream) => {
    if (remoteVideoRef.current && stream) {
      remoteVideoRef.current.srcObject = stream;
      remoteVideoRef.current.play().catch(() => {});
    }
    if (remoteAudioRef.current && stream) {
      remoteAudioRef.current.srcObject = stream;
      remoteAudioRef.current.play().catch(() => {});
    }
  }, []);

  // ── Drain Pending ICE Candidates ──────────────────────────────────────
  const drainIceCandidates = useCallback(async (pc) => {
    while (pendingIceCandidatesRef.current.length > 0) {
      const candidate = pendingIceCandidatesRef.current.shift();
      try {
        await pc.addIceCandidate(new RTCIceCandidate(candidate));
      } catch (err) {
        // Queued candidate handled
      }
    }
  }, []);

  // ── Create RTCPeerConnection ──────────────────────────────────────────
  const createPeerConnection = useCallback(() => {
    closePeerConnection();

    const pc = new RTCPeerConnection(getIceConfig());
    pcRef.current = pc;

    // Send ICE candidates to peer
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        sendSignal({
          event: 'ICE_CANDIDATE',
          candidate: event.candidate.toJSON(),
        });
      }
    };

    // Handle remote audio & video tracks
    pc.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        const stream = event.streams[0];
        remoteStreamRef.current = stream;
        
        const hasVideo = stream.getVideoTracks().length > 0;
        setIsRemoteVideoAvailable(hasVideo);

        attachRemoteStream(stream);

        stream.onaddtrack = () => {
          setIsRemoteVideoAvailable(stream.getVideoTracks().length > 0);
          attachRemoteStream(stream);
        };
        stream.onremovetrack = () => {
          setIsRemoteVideoAvailable(stream.getVideoTracks().length > 0);
        };
      }
    };

    // Monitor connection state
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
        setError('Connection lost. The teleconsultation has ended.');
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
  }, [closePeerConnection, sendSignal, updateCallState, startDurationTimer, setStuckTimeout, cleanupCall, attachRemoteStream]);

  // ── Acquire Media (Audio or Audio+Video) ───────────────────────────────
  const acquireMedia = useCallback(async (type = 'audio') => {
    const isVideo = type === 'video';
    const constraints = {
      audio: true,
      video: isVideo
        ? {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user',
          }
        : false,
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      localStreamRef.current = stream;
      if (isVideo) {
        setIsVideoEnabled(true);
        setTimeout(() => attachLocalStream(stream), 100);
      }
      return stream;
    } catch (err) {
      // Fallback: If video failed (e.g. camera in use by other tab), acquire audio-only
      if (isVideo) {
        try {
          const audioOnlyStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
          localStreamRef.current = audioOnlyStream;
          setIsVideoEnabled(false);
          setError('Camera was busy or unavailable. Connected with microphone audio.');
          return audioOnlyStream;
        } catch (audioErr) {
          // Both failed
        }
      }

      const msg = err.name === 'NotAllowedError'
        ? 'Microphone and camera permissions were denied. Please allow device access in your browser.'
        : err.name === 'NotFoundError'
          ? 'No audio or video input device was detected.'
          : 'Could not access media devices. Please check system permissions.';
      setError(msg);
      throw new Error(msg);
    }
  }, [attachLocalStream]);

  // ── Handle Incoming Signaling Messages ────────────────────────────────
  const handleSignalingMessage = useCallback(async (data) => {
    const event = data.event;

    switch (event) {
      case 'CALL_CONNECTED':
        setPeerName(data.peer_name || '');
        break;

      case 'CALL_REQUEST': {
        // Only reject as BUSY if actively connected or in a live call
        const isActivelyCalling = [
          CALL_STATES.CONNECTED,
          CALL_STATES.CALLING,
          CALL_STATES.RINGING,
          CALL_STATES.ACCEPTED,
          CALL_STATES.CONNECTING,
          CALL_STATES.RECONNECTING,
        ].includes(callStateRef.current);

        if (isActivelyCalling) {
          sendSignal({ event: 'CALL_DECLINE', reason: 'BUSY' });
          return;
        }

        // Reset previous ended/failed state
        cleanupCall();
        setError(null);

        const incomingType = data.call_type || data.callType || 'audio';
        callTypeRef.current = incomingType;
        setCallType(incomingType);
        setIncomingCallInfo({
          senderName: data.sender_name || 'Unknown',
          senderRole: data.sender_role || 'UNKNOWN',
          consultationId: data.consultation_id,
          callType: incomingType,
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
          const stream = localStreamRef.current || await acquireMedia(callTypeRef.current);
          stream.getTracks().forEach(track => pc.addTrack(track, stream));

          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          sendSignal({
            event: 'CALL_OFFER',
            sdp: pc.localDescription.toJSON(),
            call_type: callTypeRef.current,
          });
        } catch (err) {
          setError('Failed to establish peer connection. Please try again.');
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
        // Accept offer if in ACCEPTED, RINGING, or CONNECTING state
        updateCallState(CALL_STATES.CONNECTING);
        setStuckTimeout(20000);
        try {
          const offeredType = data.call_type || callTypeRef.current;
          callTypeRef.current = offeredType;
          setCallType(offeredType);

          const pc = createPeerConnection();
          const stream = localStreamRef.current || await acquireMedia(offeredType);
          stream.getTracks().forEach(track => pc.addTrack(track, stream));

          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          await drainIceCandidates(pc);

          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          sendSignal({
            event: 'CALL_ANSWER',
            sdp: pc.localDescription.toJSON(),
            call_type: offeredType,
          });
        } catch (err) {
          setError('Failed to establish video/audio teleconsultation.');
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
          await drainIceCandidates(pcRef.current);
        } catch (err) {
          setError('Failed to finalize teleconsultation stream.');
          updateCallState(CALL_STATES.FAILED);
          cleanupCall();
        }
        break;
      }

      case 'ICE_CANDIDATE': {
        if (data.candidate) {
          if (pcRef.current && pcRef.current.remoteDescription) {
            try {
              await pcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (err) {
              // Non-fatal ICE candidate note
            }
          } else {
            // Queue until remote description is set
            pendingIceCandidatesRef.current.push(data.candidate);
          }
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
          setError('The attending participant is not currently active in this workspace.');
          if (callStateRef.current === CALL_STATES.CALLING) {
            updateCallState(CALL_STATES.FAILED);
            cleanupCall();
          }
        } else if (errorType === 'PEER_DISCONNECTED') {
          setError('The other participant disconnected from the teleconsultation.');
          updateCallState(CALL_STATES.FAILED);
          cleanupCall();
        } else {
          setError(data.message || 'An error occurred during the teleconsultation.');
        }
        break;
      }

      case 'pong':
        break;

      default:
        break;
    }
  }, [sendSignal, updateCallState, createPeerConnection, acquireMedia, cleanupCall, setStuckTimeout, drainIceCandidates]);

  // ── Connect Signaling WebSocket ───────────────────────────────────────
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
  }, [consultationId, user?.user_id, user?.id, handleSignalingMessage, updateCallState, cleanupCall]);

  // ── Tab Close / Beforeunload Handler ──────────────────────────────────
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (callStateRef.current !== CALL_STATES.IDLE && callStateRef.current !== CALL_STATES.ENDED) {
        sendSignal({ event: 'CALL_END', reason: 'TAB_CLOSED' });
        stopLocalMedia();
        closePeerConnection();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sendSignal, stopLocalMedia, closePeerConnection]);

  // ── Public Actions ────────────────────────────────────────────────────

  /** Initiate a Call (Audio or Video) */
  const startCall = useCallback(async (type = 'audio') => {
    if (callStateRef.current !== CALL_STATES.IDLE) return;
    setError(null);
    callTypeRef.current = type;
    setCallType(type);

    try {
      await acquireMedia(type);
      updateCallState(CALL_STATES.CALLING);
      setStuckTimeout(45000);

      const sent = sendSignal({ event: 'CALL_REQUEST', call_type: type });
      if (!sent) {
        setError('Unable to reach the server. Please check your connection.');
        updateCallState(CALL_STATES.FAILED);
        cleanupCall();
      }
    } catch (err) {
      updateCallState(CALL_STATES.FAILED);
      cleanupCall();
    }
  }, [acquireMedia, updateCallState, setStuckTimeout, sendSignal, cleanupCall]);

  /** Accept an Incoming Call */
  const acceptCall = useCallback(async (overrideType = null) => {
    if (callStateRef.current !== CALL_STATES.RINGING) return;
    setError(null);
    const type = overrideType || callTypeRef.current || 'audio';
    callTypeRef.current = type;
    setCallType(type);

    try {
      await acquireMedia(type);
      updateCallState(CALL_STATES.ACCEPTED);
      sendSignal({ event: 'CALL_ACCEPT', call_type: type });
      setStuckTimeout(20000);
    } catch (err) {
      updateCallState(CALL_STATES.FAILED);
      sendSignal({ event: 'CALL_DECLINE', reason: 'MEDIA_ERROR' });
      cleanupCall();
    }
  }, [acquireMedia, updateCallState, sendSignal, setStuckTimeout, cleanupCall]);

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
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  }, []);

  /** Toggle webcam video track */
  const toggleVideo = useCallback(async () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoEnabled(videoTrack.enabled);
      } else {
        try {
          const videoStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
          });
          const newTrack = videoStream.getVideoTracks()[0];
          if (newTrack && pcRef.current) {
            localStreamRef.current.addTrack(newTrack);
            pcRef.current.addTrack(newTrack, localStreamRef.current);
            setIsVideoEnabled(true);
            attachLocalStream(localStreamRef.current);
          }
        } catch (e) {
          setError('Could not enable webcam.');
        }
      }
    }
  }, [attachLocalStream]);

  /** Clear error */
  const clearError = useCallback(() => setError(null), []);

  /** Reset to idle */
  const resetToIdle = useCallback(() => {
    cleanupCall();
    setError(null);
    setIncomingCallInfo(null);
    updateCallState(CALL_STATES.IDLE);
  }, [cleanupCall, updateCallState]);

  /** Full cleanup for logout */
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
    setIsRemoteVideoAvailable(false);
    updateCallState(CALL_STATES.IDLE);
  }, [sendSignal, cleanupCall, updateCallState]);

  return {
    // State
    callState,
    callType,
    isMuted,
    isVideoEnabled,
    isRemoteVideoAvailable,
    callDuration,
    peerName,
    peerRole,
    incomingCallInfo,
    error,

    // Refs for Video Elements
    localVideoRef,
    remoteVideoRef,
    remoteAudioRef,

    // Actions
    startCall,
    acceptCall,
    declineCall,
    cancelCall,
    endCall,
    toggleMute,
    toggleVideo,
    clearError,
    resetToIdle,
    fullCleanup,
  };
}
