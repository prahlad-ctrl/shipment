import { useState, useRef, useEffect } from 'react';
import { Ship, Lock, Mail, ArrowRight, User, ShieldCheck, KeyRound } from 'lucide-react';
import { signupUser, loginUser, verifyOTP, googleLogin } from '../utils/api';
import { auth, googleProvider } from '../utils/firebase';
import { signInWithPopup } from 'firebase/auth';

export default function Login({ onLogin }) {
  const [step, setStep] = useState('auth'); // 'auth' | 'otp'
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const otpRefs = useRef([]);

  // Focus first OTP input when step changes to otp
  useEffect(() => {
    if (step === 'otp' && otpRefs.current[0]) {
      otpRefs.current[0].focus();
    }
  }, [step]);

  const handleOtpChange = (index, value) => {
    if (value.length > 1) value = value.slice(-1);
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    for (let i = 0; i < pasted.length; i++) {
      newOtp[i] = pasted[i];
    }
    setOtp(newOtp);
    const nextEmpty = Math.min(pasted.length, 5);
    otpRefs.current[nextEmpty]?.focus();
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password || (isSignUp && !name)) {
      setError('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      if (isSignUp) {
        await signupUser(name, email, password);
        setSuccess('Account created! Please sign in.');
        setIsSignUp(false);
        setName('');
        setPassword('');
      } else {
        const result = await loginUser(email, password);
        if (result.mfa_required) {
          setStep('otp');
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const result = await verifyOTP(email, otpCode);
      // Store tokens
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('refresh_token', result.refresh_token);
      localStorage.setItem('user', JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
      setOtp(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '14px 14px 14px 44px',
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--glass-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: 'var(--font-size-base)',
    outline: 'none',
    transition: 'all var(--transition-base)',
    fontFamily: 'var(--font-family)',
  };

  const handleFocus = (e) => {
    e.target.style.borderColor = 'var(--accent-blue)';
    e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.12)';
    e.target.style.background = 'rgba(255, 255, 255, 0.05)';
  };

  const handleBlur = (e) => {
    e.target.style.borderColor = 'var(--glass-border)';
    e.target.style.boxShadow = 'none';
    e.target.style.background = 'rgba(255, 255, 255, 0.03)';
  };

  return (
    <>
      <div className="bg-gradient-orbs" />
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', padding: 'var(--space-xl)',
        position: 'relative', zIndex: 1
      }}>
        <div className="glass-card animate-fade-in-up" style={{
          width: '100%', maxWidth: '440px', padding: 'var(--space-2xl)',
          position: 'relative', overflow: 'hidden'
        }}>
          {/* Top accent line */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
            background: step === 'otp' ? 'var(--gradient-success)' : 'var(--gradient-accent)'
          }} />

          {/* ─── AUTH STEP ─── */}
          {step === 'auth' && (
            <>
              {/* Header */}
              <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
                <div style={{
                  width: '64px', height: '64px', margin: '0 auto var(--space-md)',
                  background: 'var(--gradient-accent)', borderRadius: 'var(--radius-xl)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: 'var(--shadow-glow-blue)'
                }}>
                  <Ship size={32} color="white" />
                </div>
                <h1 style={{
                  fontSize: 'var(--font-size-2xl)', fontWeight: 700,
                  color: 'var(--text-primary)', letterSpacing: '-0.02em',
                  marginBottom: 'var(--space-xs)'
                }}>
                  {isSignUp ? 'Create Account' : 'ShipRoute AI'}
                </h1>
                <p style={{ color: 'var(--text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
                  {isSignUp ? 'Join the intelligent shipment network' : 'Intelligent Shipment Orchestration'}
                </p>
              </div>

              {/* Form */}
              <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>

                {error && (
                  <div className="animate-fade-in" style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)',
                    borderRadius: 'var(--radius-md)', color: 'var(--accent-rose)',
                    fontSize: 'var(--font-size-sm)', textAlign: 'center'
                  }}>{error}</div>
                )}

                {success && (
                  <div className="animate-fade-in" style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: 'var(--radius-md)', color: 'var(--accent-emerald)',
                    fontSize: 'var(--font-size-sm)', textAlign: 'center'
                  }}>{success}</div>
                )}

                {isSignUp && (
                  <div style={{ position: 'relative' }}>
                    <User size={18} style={{
                      position: 'absolute', left: 'var(--space-md)', top: '50%',
                      transform: 'translateY(-50%)', color: 'var(--text-tertiary)'
                    }} />
                    <input type="text" placeholder="Full Name / Company" value={name}
                      onChange={(e) => setName(e.target.value)}
                      style={inputStyle} onFocus={handleFocus} onBlur={handleBlur} />
                  </div>
                )}

                <div style={{ position: 'relative' }}>
                  <Mail size={18} style={{
                    position: 'absolute', left: 'var(--space-md)', top: '50%',
                    transform: 'translateY(-50%)', color: 'var(--text-tertiary)'
                  }} />
                  <input type="email" placeholder="Email Address" value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={inputStyle} onFocus={handleFocus} onBlur={handleBlur} />
                </div>

                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{
                    position: 'absolute', left: 'var(--space-md)', top: '50%',
                    transform: 'translateY(-50%)', color: 'var(--text-tertiary)'
                  }} />
                  <input type="password" placeholder="Password" value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={inputStyle} onFocus={handleFocus} onBlur={handleBlur} />
                </div>

                <button type="submit" disabled={isLoading} style={{
                  marginTop: 'var(--space-sm)', width: '100%', padding: '14px',
                  border: 'none', borderRadius: 'var(--radius-md)',
                  background: 'var(--gradient-accent)', color: 'white',
                  fontSize: 'var(--font-size-base)', fontWeight: 600,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  gap: 'var(--space-sm)', boxShadow: 'var(--shadow-glow-blue)',
                  transition: 'all var(--transition-fast)', opacity: isLoading ? 0.7 : 1,
                  fontFamily: 'var(--font-family)',
                }}>
                  {isLoading ? (
                    <span className="spinner" style={{
                      width: '20px', height: '20px', border: '2px solid rgba(255,255,255,0.3)',
                      borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite'
                    }} />
                  ) : (
                    <>{isSignUp ? 'Sign Up' : 'Sign In'} <ArrowRight size={18} /></>
                  )}
                </button>
              </form>

              {/* Divider */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-md)',
                margin: 'var(--space-lg) 0'
              }}>
                <div style={{ flex: 1, height: '1px', background: 'var(--glass-border)' }} />
                <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)', whiteSpace: 'nowrap' }}>or continue with</span>
                <div style={{ flex: 1, height: '1px', background: 'var(--glass-border)' }} />
              </div>

              {/* Google Sign In */}
              <button
                type="button"
                disabled={isLoading}
                onClick={async () => {
                  setIsLoading(true);
                  setError('');
                  try {
                    const result = await signInWithPopup(auth, googleProvider);
                    const idToken = await result.user.getIdToken();
                    const res = await googleLogin(
                      idToken,
                      result.user.displayName || '',
                      result.user.email
                    );
                    localStorage.setItem('access_token', res.access_token);
                    localStorage.setItem('refresh_token', res.refresh_token);
                    localStorage.setItem('user', JSON.stringify(res.user));
                    onLogin(res.user);
                  } catch (err) {
                    if (err.code === 'auth/popup-closed-by-user') return;
                    const messages = {
                      'auth/configuration-not-found': 'Google Sign-In is not enabled. Please enable it in Firebase Console → Authentication → Sign-in method.',
                      'auth/network-request-failed': 'Network error. Check your connection.',
                      'auth/too-many-requests': 'Too many attempts. Please wait and retry.',
                      'auth/popup-blocked': 'Popup was blocked by browser. Please allow popups.',
                    };
                    setError(messages[err.code] || err.message);
                  } finally {
                    setIsLoading(false);
                  }
                }}
                style={{
                  width: '100%', padding: '12px', border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.04)',
                  color: 'var(--text-primary)', fontSize: 'var(--font-size-sm)', fontWeight: 500,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                  transition: 'all var(--transition-fast)', fontFamily: 'var(--font-family)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Sign in with Google
              </button>

              {/* Toggle */}
              <div style={{ textAlign: 'center', marginTop: 'var(--space-lg)' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  {isSignUp ? 'Already have an account?' : "Don't have an account?"}
                </span>
                <button onClick={() => { setIsSignUp(!isSignUp); setError(''); setSuccess(''); }}
                  style={{
                    background: 'none', border: 'none', color: 'var(--accent-blue)',
                    fontWeight: 600, fontSize: 'var(--font-size-sm)', marginLeft: '8px',
                    cursor: 'pointer', fontFamily: 'inherit'
                  }}>
                  {isSignUp ? 'Sign In' : 'Sign Up'}
                </button>
              </div>
            </>
          )}

          {/* ─── OTP STEP ─── */}
          {step === 'otp' && (
            <>
              <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
                <div style={{
                  width: '64px', height: '64px', margin: '0 auto var(--space-md)',
                  background: 'var(--gradient-success)', borderRadius: 'var(--radius-xl)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: 'var(--shadow-glow-emerald)'
                }}>
                  <ShieldCheck size={32} color="white" />
                </div>
                <h1 style={{
                  fontSize: 'var(--font-size-2xl)', fontWeight: 700,
                  color: 'var(--text-primary)', letterSpacing: '-0.02em',
                  marginBottom: 'var(--space-xs)'
                }}>
                  Verify Identity
                </h1>
                <p style={{ color: 'var(--text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
                  Enter the 6-digit code sent to
                </p>
                <p style={{ color: 'var(--accent-blue)', fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
                  {email}
                </p>
              </div>

              <form onSubmit={handleOtpSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>

                {error && (
                  <div className="animate-fade-in" style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)',
                    borderRadius: 'var(--radius-md)', color: 'var(--accent-rose)',
                    fontSize: 'var(--font-size-sm)', textAlign: 'center'
                  }}>{error}</div>
                )}

                {/* OTP Input Grid */}
                <div style={{
                  display: 'flex', gap: 'var(--space-sm)', justifyContent: 'center'
                }} onPaste={handleOtpPaste}>
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      ref={el => otpRefs.current[i] = el}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      style={{
                        width: '52px', height: '60px', textAlign: 'center',
                        fontSize: '1.5rem', fontWeight: 700,
                        background: digit ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                        border: `2px solid ${digit ? 'var(--accent-blue)' : 'var(--glass-border)'}`,
                        borderRadius: 'var(--radius-md)', color: 'var(--text-primary)',
                        outline: 'none', transition: 'all var(--transition-fast)',
                        fontFamily: 'var(--font-family)',
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = 'var(--accent-blue)';
                        e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.15)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = digit ? 'var(--accent-blue)' : 'var(--glass-border)';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                  ))}
                </div>

                <button type="submit" disabled={isLoading || otp.join('').length !== 6} style={{
                  width: '100%', padding: '14px', border: 'none',
                  borderRadius: 'var(--radius-md)', background: 'var(--gradient-success)',
                  color: 'white', fontSize: 'var(--font-size-base)', fontWeight: 600,
                  cursor: (isLoading || otp.join('').length !== 6) ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  gap: 'var(--space-sm)', boxShadow: 'var(--shadow-glow-emerald)',
                  transition: 'all var(--transition-fast)',
                  opacity: (isLoading || otp.join('').length !== 6) ? 0.6 : 1,
                  fontFamily: 'var(--font-family)',
                }}>
                  {isLoading ? (
                    <span className="spinner" style={{
                      width: '20px', height: '20px', border: '2px solid rgba(255,255,255,0.3)',
                      borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite'
                    }} />
                  ) : (
                    <><KeyRound size={18} /> Verify & Access</>
                  )}
                </button>

                <button type="button" onClick={() => { setStep('auth'); setOtp(['','','','','','']); setError(''); }}
                  style={{
                    background: 'none', border: 'none', color: 'var(--text-secondary)',
                    fontSize: 'var(--font-size-sm)', cursor: 'pointer', textAlign: 'center',
                    fontFamily: 'inherit'
                  }}>
                  ← Back to Sign In
                </button>
              </form>
            </>
          )}

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 'var(--space-xl)' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
              {step === 'otp' ? '🔒 Multi-Factor Authentication' : 'Secure AI Agent Protocol'} • v1.0.0
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
