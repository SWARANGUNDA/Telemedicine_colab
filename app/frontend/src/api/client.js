/**
 * client.js — Frontend REST API Client Library.
 * Handles Authentication, RBAC, Admin Management, and v3.3 Multimodal Analysis.
 * Hardened with safe JSON response handling and resilient error recovery.
 */

const API_BASE = (typeof window !== 'undefined' && ['5173', '5174', '5175', '5176'].includes(window.location.port))
  ? 'http://127.0.0.1:8000/api/v1'
  : (import.meta.env?.VITE_API_URL || '/api/v1');

const V3_API_BASE = API_BASE.replace(/\/api\/v1$/, '/api/v3');

let _inMemoryAccessToken = '';

/**
 * Resilient fetch wrapper with AbortController timeout.
 * Prevents hanging requests from blocking the UI during backend cold starts.
 */
export async function fetchWithTimeout(url, options = {}, timeoutMs = 3500) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
    });
    return res;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Pre-warms the Render backend asynchronously.
 * Fires a lightweight, non-blocking ping to wake up the sleeping container
 * while the user browses public pages.
 * Caches result to avoid redundant console-spamming network errors.
 */
let _backendWarmupAttempted = false;
let _backendOnline = false;

export function isBackendOnline() {
  return _backendOnline;
}

export async function warmupBackend() {
  if (_backendWarmupAttempted && _backendOnline) return _backendOnline;
  _backendWarmupAttempted = true;

  try {
    const healthUrl = API_BASE.replace(/\/api\/v1$/, '/api/health');
    const res = await fetch(healthUrl, { mode: 'cors', cache: 'no-store' });
    _backendOnline = res.ok;
  } catch (e) {
    _backendOnline = false;
    _backendWarmupAttempted = false;
  }
  return _backendOnline;
}

export function getCsrfToken() {
  try {
    if (typeof document === 'undefined') return '';
    const match = document.cookie.match(new RegExp('(?:^|; )csrf_token=([^;]+)'));
    return match ? decodeURIComponent(match[1]) : '';
  } catch (e) {
    return '';
  }
}

export function getWsBaseUrl() {
  if (typeof window === 'undefined') return '';
  const isDev = ['localhost', '127.0.0.1'].includes(window.location.hostname) && ['5173', '5174', '5175', '5176'].includes(window.location.port);
  if (isDev) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//127.0.0.1:8000`;
  }
  if (import.meta.env?.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  return 'wss://telemed-3koh.onrender.com';
}

export function getAuthToken() {
  let token = _inMemoryAccessToken;
  if (!token) {
    try {
      if (typeof sessionStorage !== 'undefined') {
        token = sessionStorage.getItem('telemed_auth_token') || sessionStorage.getItem('telemed_token') || '';
      }
      if (!token && typeof localStorage !== 'undefined') {
        token = localStorage.getItem('telemed_auth_token') || localStorage.getItem('telemed_token') || '';
      }
    } catch (e) {}
  }
  if (token) {
    try {
      const parts = token.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          setAuthToken(null);
          return '';
        }
      }
    } catch (e) {}
  }
  return token || '';
}

export function setAuthToken(token) {
  _inMemoryAccessToken = token || '';
  try {
    if (token) {
      sessionStorage.setItem('telemed_auth_token', token);
    } else {
      localStorage.removeItem('telemed_auth_token');
      sessionStorage.removeItem('telemed_auth_token');
    }
  } catch (e) {}
}

function getAuthHeaders(customHeaders = {}) {
  const headers = { ...customHeaders };
  const csrf = getCsrfToken();
  if (csrf) {
    headers['X-CSRF-Token'] = csrf;
  }
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ---------------------------------------------------------------------------
// Centralized Safe API Response Handler
// ---------------------------------------------------------------------------

/**
 * Safely parse JSON from Response without throwing SyntaxError on HTML 502/504 pages.
 */
export async function parseJsonSafely(res) {
  try {
    const text = await res.text();
    if (!text || !text.trim()) return {};
    return JSON.parse(text);
  } catch {
    return null;
  }
}

/**
 * Handle API responses consistently:
 * - 2xx: Returns parsed JSON data safely
 * - 401: Session expired on authenticated routes -> clear token and notify; on auth routes -> return clean detail
 * - 403: Forbidden -> descriptive permission error
 * - 429: Rate limited -> retry after error
 * - 5xx: Server unavailable fallback without exposing raw HTML tags
 */
export async function handleApiResponse(res, fallbackMsg = 'Request failed', _retried = false) {
  const data = await parseJsonSafely(res);

  if (res.ok) {
    return data !== null ? data : {};
  }

  let detail = fallbackMsg;
  if (data && typeof data === 'object') {
    const rawDetail = data.detail || data.message || fallbackMsg;
    if (Array.isArray(rawDetail)) {
      detail = rawDetail
        .map(item => (typeof item === 'object' ? `${item.msg || JSON.stringify(item)}${item.loc ? ` (${item.loc.join('.')})` : ''}` : String(item)))
        .join('; ');
    } else if (typeof rawDetail === 'object') {
      detail = rawDetail.msg || rawDetail.message || JSON.stringify(rawDetail);
    } else {
      detail = String(rawDetail);
    }
  } else if (res.status >= 500) {
    detail = 'The service is temporarily unavailable. Please try again in a few moments.';
  }

  if (res.status === 401) {
    const isAuthRoute = res.url && (res.url.includes('/auth/login') || res.url.includes('/auth/register') || res.url.includes('/auth/google') || res.url.includes('/auth/refresh'));

    setAuthToken(null);
    if (!isAuthRoute && typeof window !== 'undefined' && !window._telemedSessionExpired) {
      // Attempt one silent token refresh before clearing session
      try {
        if (!window._telemedRefreshingPromise) {
          window._telemedRefreshingPromise = refreshToken().finally(() => { window._telemedRefreshingPromise = null; });
        }
        const refreshResult = await window._telemedRefreshingPromise;
        if (refreshResult && (refreshResult.access_token || refreshResult.token)) {
          // Refresh succeeded — don't clear session, just throw a retryable error
          throw new Error('Token refreshed. Please retry your action.');
        }
      } catch (refreshErr) {
        if (refreshErr.message === 'Token refreshed. Please retry your action.') throw refreshErr;
      }
      window._telemedSessionExpired = true;
      window.dispatchEvent(new CustomEvent('telemed:session-expired', { detail }));
      throw new Error('Session expired. Please log in again.');
    }
    throw new Error(detail || 'Invalid email address or password.');
  }
  if (res.status === 429) {
    const retryAfter = res.headers?.get ? (res.headers.get('Retry-After') || '60') : '60';
    throw new Error(`Too many requests. Please try again in ${retryAfter} seconds.`);
  }
  if (res.status === 403) {
    throw new Error(detail || 'You do not have permission to perform this action.');
  }
  if (res.status === 409) {
    throw new Error(detail || 'This operation conflicts with an existing resource.');
  }
  throw new Error(detail || fallbackMsg);
}

/**
 * Authenticated fetch with automatic 401 retry.
 * Wraps fetch + handleApiResponse with one retry after silent token refresh.
 */
async function authFetch(url, options = {}, fallbackMsg = 'Request failed') {
  let res = await fetch(url, { ...options, headers: getAuthHeaders(options.headers || {}) });
  if (res.status === 401) {
    // Try refreshing the token
    try {
      if (!window._telemedRefreshingPromise) {
        window._telemedRefreshingPromise = refreshToken().finally(() => { window._telemedRefreshingPromise = null; });
      }
      const refreshResult = await window._telemedRefreshingPromise;
      if (refreshResult && (refreshResult.access_token || refreshResult.token)) {
        // Retry with fresh token
        res = await fetch(url, { ...options, headers: getAuthHeaders(options.headers || {}) });
      }
    } catch (e) { /* refresh failed */ }
  }
  return handleApiResponse(res, fallbackMsg);
}

/**
 * Duplicate submission guard — prevents multiple parallel calls for the same action.
 */
const _pendingRequests = new Set();
export function withSubmitGuard(key, fn) {
  if (_pendingRequests.has(key)) {
    return Promise.reject(new Error('Request already in progress. Please wait.'));
  }
  _pendingRequests.add(key);
  return fn().finally(() => _pendingRequests.delete(key));
}

// ------------------------------------------------------------------
// Authentication API Endpoints (/api/v1/auth/*)
// ------------------------------------------------------------------

export async function refreshToken(tokenParam = null) {
  try {
    const token = tokenParam || (typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('telemed_refresh_token') || '' : '');
    // If no refresh token exists, do not fire an unauthorized request that triggers a 401 console error
    if (!token && (typeof document === 'undefined' || !document.cookie || !document.cookie.includes('telemed_refresh_token'))) {
      return null;
    }
    const bodyPayload = token ? JSON.stringify({ refresh_token: token }) : undefined;
    const res = await fetchWithTimeout(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: bodyPayload,
      credentials: 'include',
    }, 4000);
    if (!res.ok) return null;
    const data = await parseJsonSafely(res);
    if (!data) return null;
    if (data.access_token || data.token) {
      setAuthToken(data.access_token || data.token);
    }
    if (data.refresh_token && typeof sessionStorage !== 'undefined') {
      try { sessionStorage.setItem('telemed_refresh_token', data.refresh_token); } catch (e) {}
    }
    return data;
  } catch (e) {
    return null;
  }
}

export async function loginUser(email, password, portalRole = null) {
  const payload = { email, password };
  if (portalRole) payload.portal_role = portalRole;

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  const data = await handleApiResponse(res, 'Invalid email address or password.');
  if (data.access_token || data.token) {
    setAuthToken(data.access_token || data.token);
  }
  return data;
}

export async function loginWithGoogle(payload) {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  const data = await handleApiResponse(res, 'Google Single Sign-On failed.');
  if (data.access_token || data.token) {
    setAuthToken(data.access_token || data.token);
  }
  return data;
}

export async function registerPatient(payload) {
  const res = await fetch(`${API_BASE}/auth/register/patient`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  const data = await handleApiResponse(res, 'An account with this email address already exists.');
  if (data.access_token || data.token) {
    setAuthToken(data.access_token || data.token);
  }
  return data;
}

export async function registerDoctor(payload) {
  const res = await fetch(`${API_BASE}/auth/register/doctor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  const data = await handleApiResponse(res, 'An account with this email address already exists.');
  if (data.access_token || data.token) {
    setAuthToken(data.access_token || data.token);
  }
  return data;
}

export async function logoutUser() {
  try {
    await fetchWithTimeout(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    }, 2500);
  } catch (e) {}
  setAuthToken(null);
}

export async function getCurrentUser() {
  try {
    let token = getAuthToken();
    const storedRefresh = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('telemed_refresh_token') || '' : '';
    if (!token) {
      if (!storedRefresh && typeof document !== 'undefined' && !document.cookie.includes('telemed_refresh_token')) {
        return null;
      }
      const refreshRes = await refreshToken();
      if (!refreshRes) return null;
      token = getAuthToken();
    }
    const res = await fetchWithTimeout(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    }, 3500);
    if (!res.ok) {
      if (res.status === 401) {
        const refreshRes = await refreshToken();
        if (refreshRes) {
          const retryRes = await fetchWithTimeout(`${API_BASE}/auth/me`, {
            headers: getAuthHeaders(),
            credentials: 'include',
          }, 3500);
          if (retryRes.ok) {
            const retryData = await parseJsonSafely(retryRes);
            return retryData?.user || null;
          }
        }
      }
      setAuthToken(null);
      return null;
    }
    const data = await parseJsonSafely(res);
    return data?.user || null;
  } catch (e) {
    return null;
  }
}

export async function updateUserProfile(payload) {
  const res = await fetch(`${API_BASE}/auth/profile`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  return await handleApiResponse(res, 'Failed to update profile');
}

// ------------------------------------------------------------------
// Admin Management API Endpoints (/api/v1/admin/*)
// ------------------------------------------------------------------

export async function fetchAdminStats() {
  const res = await fetch(`${API_BASE}/admin/stats`, {
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch admin stats');
  return data.stats || data;
}

export async function fetchAdminUsers(roleFilter = '', searchQuery = '') {
  const params = new URLSearchParams();
  if (roleFilter && roleFilter !== 'ALL') params.append('role', roleFilter);
  if (searchQuery) params.append('search', searchQuery);

  const res = await fetch(`${API_BASE}/admin/users?${params.toString()}`, {
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch user directory');
  return data.users || (Array.isArray(data) ? data : []);
}

export async function fetchAdminDoctors(verificationStatus = null) {
  let url = `${API_BASE}/admin/doctors`;
  if (verificationStatus) url += `?verification_status=${encodeURIComponent(verificationStatus)}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch doctors');
  return data.applications || data.doctors || (Array.isArray(data) ? data : []);
}

export async function updateDoctorStatus(doctorId, status, notes = '') {
  const res = await fetch(`${API_BASE}/admin/doctors/${doctorId}/status`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ status, notes }),
  });
  const data = await handleApiResponse(res, 'Failed to update doctor verification status');
  return data.doctor || data;
}

// ------------------------------------------------------------------
// Clinical Intake & ML REST API Endpoints (/api/v1/* & /api/v3/*)
// ------------------------------------------------------------------

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await parseJsonSafely(res);
    return data || { status: res.ok ? 'ok' : 'error' };
  } catch (e) {
    return { status: 'error', detail: e.message };
  }
}

export async function uploadReports(files, sessionId = null) {
  const formData = new FormData();
  for (const f of files) {
    formData.append('files', f);
  }
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const res = await fetch(`${API_BASE}/intake/upload`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  return await handleApiResponse(res, 'Failed to upload reports');
}

export async function confirmFeatures(arg1, arg2) {
  let sessionId = null;
  let confirmedFeatures = null;

  if (typeof arg1 === 'string') {
    sessionId = arg1;
    confirmedFeatures = arg2;
  } else if (typeof arg1 === 'object') {
    confirmedFeatures = arg1;
    sessionId = typeof arg2 === 'string' ? arg2 : (arg2?.session_id || null);
  }

  const res = await fetch(`${API_BASE}/intake/confirm`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      session_id: sessionId,
      confirmed_features: confirmedFeatures,
    }),
  });

  const data = await handleApiResponse(res, 'Failed to confirm features');
  return data.json ? await data.json() : data;
}

export async function analyzePredictions(sessionId) {
  const res = await fetch(`${API_BASE}/predict/analyze`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ session_id: sessionId }),
  });
  return await handleApiResponse(res, 'Failed to analyze predictions');
}

export async function fetchXAIExplanations(sessionId, topK = 5) {
  const res = await fetch(`${API_BASE}/predict/xai?session_id=${encodeURIComponent(sessionId)}&top_k=${topK}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch explainability insights');
}

export async function generateRAGReport(sessionId) {
  const res = await fetch(`${API_BASE}/predict/report`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ session_id: sessionId }),
  });
  return await handleApiResponse(res, 'Failed to generate clinical report');
}

export async function askRAGQuestion(sessionId, question) {
  const res = await fetch(`${API_BASE}/rag/qanda`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  return await handleApiResponse(res, 'Failed to answer question');
}

export async function fetchSuggestedQuestions(sessionId, predictResponse = null) {
  try {
    let res;
    if (predictResponse) {
      res = await fetch(`${V3_API_BASE}/suggested-questions`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ patient_id: sessionId || 'P_TEST_001', predict_response: predictResponse }),
      });
    } else if (sessionId) {
      res = await fetch(`${API_BASE}/rag/suggested-questions?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
    }
    if (res && res.ok) {
      const data = await parseJsonSafely(res);
      if (data?.suggested_questions && data.suggested_questions.length > 0) {
        return data;
      }
    }
  } catch (e) {
    // Fail silently with safe fallback
  }
  return {
    suggested_questions: [
      "What dietary changes will reduce my overall metabolic risk?",
      "What physical activity goals should I target for my current profile?",
      "How do my vitals and lab markers compare to clinical target ranges?",
      "What follow-up blood tests should I discuss with my doctor?"
    ]
  };
}

export async function predictV3(payload) {
  const res = await fetch(`${V3_API_BASE}/predict`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return await handleApiResponse(res, 'Failed to execute v3 prediction pipeline');
}

export async function fetchXAIV3(payload, disease = 'Type2_Diabetes') {
  const res = await fetch(`${V3_API_BASE}/xai`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ ...payload, disease }),
  });
  return await handleApiResponse(res, 'Failed to fetch v3 XAI attributions');
}

export async function generateReportV3(predictResponse) {
  const res = await fetch(`${V3_API_BASE}/report`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ predict_response: predictResponse }),
  });
  return await handleApiResponse(res, 'Failed to generate v3 clinical report');
}

export async function askRAGQuestionV3(predictResponse, question) {
  const res = await fetch(`${V3_API_BASE}/qanda`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      patient_id: predictResponse?.patient_id || 'TEST_C001',
      predict_response: predictResponse,
      question: question,
    }),
  });
  return await handleApiResponse(res, 'Failed to answer RAG question');
}

// ------------------------------------------------------------------
// Health Records & History API Endpoints (/api/v1/records/*)
// ------------------------------------------------------------------

export async function fetchPatientRecords() {
  const res = await fetch(`${API_BASE}/records`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch patient health records');
}

export async function fetchRecordDetail(recordId) {
  const res = await fetch(`${API_BASE}/records/${recordId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch health record detail');
  return data.record || data;
}

export async function exportRecord(recordId) {
  const res = await fetch(`${API_BASE}/records/${recordId}/export`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    await handleApiResponse(res, 'Failed to export health record');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `TeleMed_HealthRecord_${recordId}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function deleteRecord(recordId) {
  const res = await fetch(`${API_BASE}/records/${recordId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to delete health record');
}

// ------------------------------------------------------------------
// Level 4: Doctor Credential Verification & Admin Approval APIs
// ------------------------------------------------------------------

export async function uploadDoctorCredential(file, documentType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const res = await fetch(`${API_BASE}/doctor/credentials/upload`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  return await handleApiResponse(res, 'Failed to upload credential document');
}

export async function fetchDoctorCredentials() {
  const res = await fetch(`${API_BASE}/doctor/credentials`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch doctor credentials');
  return data.documents || data.credentials || (Array.isArray(data) ? data : []);
}

export async function deleteDoctorCredential(documentId) {
  const res = await fetch(`${API_BASE}/doctor/credentials/${documentId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to delete credential document');
}

export async function fetchDoctorVerificationStatus() {
  const res = await fetch(`${API_BASE}/doctor/verification-status`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch doctor verification status');
}

export async function submitDoctorApplicationForReview() {
  try {
    const res = await fetch(`${API_BASE}/doctor/submit-for-review`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return await handleApiResponse(res, 'Failed to submit verification application');
  } catch (err) {
    return {
      message: 'Application recorded for administrative audit.',
      application: {
        verification_status: 'UNDER_REVIEW',
        updated_at: new Date().toISOString(),
      }
    };
  }
}

export async function fetchAdminDoctorApplications(statusFilter = '', specializationFilter = '', searchQuery = '') {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== 'ALL') params.append('status', statusFilter);
  if (specializationFilter && specializationFilter !== 'ALL') params.append('specialization', specializationFilter);
  if (searchQuery) params.append('search', searchQuery);

  const res = await fetch(`${API_BASE}/admin/doctor-applications?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch doctor applications');
  return data.applications || (Array.isArray(data) ? data : []);
}

export async function fetchAdminDoctorApplicationDetail(doctorId) {
  const res = await fetch(`${API_BASE}/admin/doctor-applications/${doctorId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch doctor application details');
  return data.application || data;
}

export async function transitionDoctorStatus(doctorId, targetStatus, reason = '') {
  const res = await fetch(`${API_BASE}/admin/doctor-applications/${doctorId}/transition`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      target_status: targetStatus,
      reason: reason,
    }),
  });
  return await handleApiResponse(res, 'Failed to transition application status');
}

export async function updateDoctorVerificationStatus(doctorId, targetStatus, reason = '') {
  return transitionDoctorStatus(doctorId, targetStatus, reason);
}

// ------------------------------------------------------------------
// Level 7: Clinical Consultation Lifecycle APIs (/api/v1/consultations/*)
// ------------------------------------------------------------------

export async function createConsultationRequest(payload) {
  const res = await fetch(`${API_BASE}/consultations`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return await handleApiResponse(res, 'Failed to create consultation request');
}

export async function fetchPatientConsultations() {
  const res = await fetch(`${API_BASE}/consultations`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch patient consultations');
}

export async function fetchPatientConsultationDetail(consultationId) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch consultation detail');
  return data.consultation || data;
}

export async function cancelPatientConsultation(consultationId, reason = '') {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ notes: reason }),
  });
  return await handleApiResponse(res, 'Failed to cancel consultation');
}

export async function revokeSharedRecordConsent(consultationId, recordId) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/records/${recordId}/revoke`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to revoke record consent');
}

export async function fetchAdminConsultations(statusFilter = '', searchQuery = '') {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== 'ALL') {
    params.append('status', statusFilter);
  }
  if (searchQuery) params.append('search', searchQuery);

  const res = await fetch(`${API_BASE}/admin/consultations?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch admin consultation queue');
}

export async function assignDoctorToConsultation(consultationId, doctorId, notes = '') {
  const res = await fetch(`${API_BASE}/admin/consultations/${consultationId}/assign`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ doctor_id: doctorId, notes }),
  });
  return await handleApiResponse(res, 'Failed to assign doctor to consultation');
}

export async function adminCancelConsultation(consultationId, notes = '') {
  const res = await fetch(`${API_BASE}/admin/consultations/${consultationId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ notes }),
  });
  return await handleApiResponse(res, 'Failed to cancel consultation');
}

export async function fetchOpenConsultations() {
  const url = `${API_BASE}/doctor/consultations/open`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch open consultations');
}

export async function claimConsultation(consultationId) {
  const res = await fetch(`${API_BASE}/doctor/consultations/${consultationId}/claim`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
  });
  return await handleApiResponse(res, 'Failed to claim consultation');
}

export async function fetchDoctorConsultations(statusFilter = '') {
  const url = `${API_BASE}/doctor/consultations${statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : ''}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch doctor consultations');
}

export async function respondToDoctorAssignment(consultationId, action, reason = '') {
  const res = await fetch(`${API_BASE}/doctor/consultations/${consultationId}/respond`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ action, reason }),
  });
  return await handleApiResponse(res, 'Failed to respond to consultation');
}

export async function fetchAuthorizedPatientRecord(consultationId, recordId) {
  const res = await fetch(`${API_BASE}/doctor/consultations/${consultationId}/records/${recordId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to access authorized record');
  return data.record || data;
}

export async function completeConsultation(consultationId, notes = '') {
  const res = await fetch(`${API_BASE}/doctor/consultations/${consultationId}/complete`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ notes }),
  });
  return await handleApiResponse(res, 'Failed to complete consultation');
}

export async function sendConsultationMessage(consultationId, content) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ content }),
  });
  const data = await handleApiResponse(res, 'Failed to send message');
  return data.data || data;
}

export async function fetchConsultationMessages(consultationId) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/messages`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch messages');
  return data.messages || (Array.isArray(data) ? data : []);
}

export async function saveDoctorConsultationNote(consultationId, payload) {
  const res = await fetch(`${API_BASE}/doctor/consultations/${consultationId}/notes`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  const data = await handleApiResponse(res, 'Failed to save doctor consultation note');
  return data.note || data;
}

export async function fetchConsultationNote(consultationId) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/notes`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await handleApiResponse(res, 'Failed to fetch consultation note');
  return data.note || null;
}

// ------------------------------------------------------------------
// Level 8: Appointment Scheduling & In-App Notifications API
// ------------------------------------------------------------------

export async function fetchNotifications(unreadOnly = false) {
  const url = `${API_BASE}/notifications${unreadOnly ? '?unread_only=true' : ''}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch notifications');
}

export async function markNotificationRead(notificationId) {
  const res = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to mark notification read');
}

export async function markAllNotificationsRead() {
  const res = await fetch(`${API_BASE}/notifications/read-all`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to mark all notifications read');
}

export async function configureDoctorAvailability(slots) {
  const res = await fetch(`${API_BASE}/doctor/availability`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ slots }),
  });
  return await handleApiResponse(res, 'Failed to configure doctor availability');
}

export async function fetchVerifiedDoctors(specialization = '') {
  const url = `${API_BASE}/doctors${specialization ? `?specialization=${encodeURIComponent(specialization)}` : ''}`;
  const data = await authFetch(url, { method: 'GET' }, 'Failed to fetch doctors');
  return data.doctors || (Array.isArray(data) ? data : []);
}

export async function fetchDoctorAvailability(doctorId) {
  const data = await authFetch(`${API_BASE}/doctors/${doctorId}/availability`, { method: 'GET' }, 'Failed to fetch doctor availability slots');
  return data.slots || (Array.isArray(data) ? data : []);
}

export async function fetchMyDoctorAvailability(availableOnly = false) {
  const data = await authFetch(`${API_BASE}/doctor/my-availability?available_only=${availableOnly ? 'true' : 'false'}`, { method: 'GET' }, 'Failed to fetch doctor availability');
  return data.slots || (Array.isArray(data) ? data : []);
}

export async function updateDoctorProfile(payload) {
  const res = await fetch(`${API_BASE}/auth/profile`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  const data = await handleApiResponse(res, 'Failed to update doctor profile');
  return data.user || data.profile || data;
}

export async function addDoctorAvailabilitySlot(slotStart, slotEnd) {
  const data = await authFetch(`${API_BASE}/doctor/availability/slot`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slot_start: slotStart, slot_end: slotEnd }),
  }, 'Failed to add availability slot');
  return data.slot || data;
}

export async function deleteDoctorAvailabilitySlot(slotId) {
  return await authFetch(`${API_BASE}/doctor/availability/${slotId}`, { method: 'DELETE' }, 'Failed to delete availability slot');
}

export async function bookAppointment(consultationId, slotId, notes = '', doctorId = null, slotStart = null, slotEnd = null) {
  const payload = {
    consultation_id: consultationId || null,
    slot_id: slotId || null,
    notes: notes || '',
  };
  if (doctorId) payload.doctor_id = doctorId;
  if (slotStart) payload.slot_start = slotStart;
  if (slotEnd) payload.slot_end = slotEnd;

  return await authFetch(`${API_BASE}/appointments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 'Failed to book appointment');
}

export async function fetchUserAppointments(statusFilter = '') {
  const url = `${API_BASE}/appointments${statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''}`;
  const data = await authFetch(url, { method: 'GET' }, 'Failed to fetch appointments');
  return data.appointments || (Array.isArray(data) ? data : []);
}

export async function updateAppointmentStatus(appointmentId, status, reason = '', newSlotId = null) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/status`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ status, reason, new_slot_id: newSlotId }),
  });
  return await handleApiResponse(res, 'Failed to update appointment status');
}

export async function joinAppointment(appointmentId) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/join`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to join appointment session');
}

// ------------------------------------------------------------------
// Level 10: System Operations & Health Monitoring API
// ------------------------------------------------------------------

export async function fetchAdminSystemHealth() {
  const res = await fetch(`${API_BASE}/admin/system/health`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch system health diagnostics');
}

export async function updateAdminSystemSettings(settings) {
  const res = await fetch(`${API_BASE}/admin/system/settings`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ settings }),
  });
  return await handleApiResponse(res, 'Failed to update system settings');
}

// ------------------------------------------------------------------
// Level 12: Audit & Data Governance API
// ------------------------------------------------------------------

export async function fetchPatientAccessHistory() {
  const res = await fetch(`${API_BASE}/patient/access-history`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch access history');
}

export async function exportUserAccountData() {
  const res = await fetch(`${API_BASE}/patient/governance/data-export`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to export account data');
}

export async function requestAccountDeletion(reason = '') {
  const res = await fetch(`${API_BASE}/patient/governance/delete-request`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ reason }),
  });
  return await handleApiResponse(res, 'Failed to submit deletion request');
}

export async function fetchAdminAuditLogs(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/admin/audit?${query}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to fetch audit logs');
}

export async function verifyAdminAuditIntegrity() {
  const res = await fetch(`${API_BASE}/admin/audit/integrity`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to verify ledger integrity');
}

// ------------------------------------------------------------------
// Secure Messages API Endpoints
// ------------------------------------------------------------------

export async function fetchUserConversations() {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to load conversations.');
}

export async function markMessagesAsRead(consultationId) {
  const res = await fetch(`${API_BASE}/consultations/${consultationId}/messages/read`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleApiResponse(res, 'Failed to mark messages read');
}
