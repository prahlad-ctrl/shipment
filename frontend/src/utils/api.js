const API_BASE = 'http://localhost:8000/api';

// ── Auth helpers ────────────────────────────────────────────────────────────

export async function signupUser(name, email, password) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Signup failed');
  return data;
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  return data;
}

export async function verifyOTP(email, otp) {
  const res = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'OTP verification failed');
  return data;
}

export async function refreshToken(refresh_token) {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Token refresh failed');
  return data;
}

export async function fetchCurrentUser(accessToken) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Not authenticated');
  return data;
}

export async function googleLogin(idToken, name, email) {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken, name, email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Google login failed');
  return data;
}

/**
 * Fetch preset example queries.
 */
export async function fetchPresets() {
  const res = await fetch(`${API_BASE}/routes/presets`);
  if (!res.ok) throw new Error('Failed to fetch presets');
  return res.json();
}

/**
 * Fetch world event options.
 */
export async function fetchWorldEvents() {
  const res = await fetch(`${API_BASE}/world-events`);
  if (!res.ok) throw new Error('Failed to fetch world events');
  return res.json();
}

/**
 * Run the shipment planning agent (non-streaming).
 */
export async function planShipment(query, worldEvent = 'normal') {
  const res = await fetch(`${API_BASE}/shipment/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, world_event: worldEvent }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to plan shipment');
  }
  return res.json();
}

/**
 * Stream the shipment planning agent via SSE.
 * Calls onStep for each reasoning step and onResult for the final result.
 */
export async function streamShipmentPlan(query, worldEvent = 'normal', chatHistory = null, parsedConstraints = null, { onStep, onResult, onError, onDone }) {
  try {
    const res = await fetch(`${API_BASE}/shipment/plan/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, world_event: worldEvent, chat_history: chatHistory, parsed_constraints: parsedConstraints }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Stream failed');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));

            if (event.type === 'reasoning_step') {
              onStep?.(event.data);
            } else if (event.type === 'final_result') {
              onResult?.(event.data);
            } else if (event.type === 'error') {
              onError?.(event.data.message);
            } else if (event.type === 'done') {
              onDone?.();
            }
          } catch {
            // Ignore malformed JSON lines
          }
        }
      }
    }

    onDone?.();
  } catch (err) {
    onError?.(err.message);
  }
}
