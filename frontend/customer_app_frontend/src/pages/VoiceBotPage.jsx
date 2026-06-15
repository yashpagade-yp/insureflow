import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";

const OFFER_URL = "http://localhost:8002/voice/offer";
const ICE_URL   = "http://localhost:8002/voice/ice";

const STATUS = {
  IDLE:         "idle",
  CONNECTING:   "connecting",
  CONNECTED:    "connected",
  SPEAKING:     "speaking",
  LISTENING:    "listening",
  DISCONNECTED: "disconnected",
  ERROR:        "error",
};

const STATUS_LABEL = {
  [STATUS.IDLE]:         "Ready to connect",
  [STATUS.CONNECTING]:   "Connecting…",
  [STATUS.CONNECTED]:    "Connected — speak to InsureFlow",
  [STATUS.SPEAKING]:     "InsureFlow is speaking…",
  [STATUS.LISTENING]:    "Listening…",
  [STATUS.DISCONNECTED]: "Disconnected",
  [STATUS.ERROR]:        "Connection failed",
};

function VoiceBotPage() {
  const [status, setStatus]       = useState(STATUS.IDLE);
  const [transcript, setTranscript] = useState([]);
  const [error, setError]         = useState(null);

  const pcRef        = useRef(null);    // RTCPeerConnection
  const sessionIdRef = useRef(null);
  const audioRef     = useRef(null);    // <audio> element for bot voice

  // Cleanup on unmount
  useEffect(() => () => disconnect(), []);

  async function connect() {
    setError(null);
    setStatus(STATUS.CONNECTING);
    setTranscript([]);

    try {
      // 1. Create WebRTC peer connection
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;

      // 2. Add microphone track
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));

      // 3. Receive bot audio → play via <audio>
      pc.ontrack = (event) => {
        if (audioRef.current && event.streams[0]) {
          audioRef.current.srcObject = event.streams[0];
        }
      };

      // 4. Create SDP offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // 5. Send offer to bot server
      const res = await fetch(OFFER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
      });
      if (!res.ok) throw new Error(`Offer failed: ${res.status}`);

      const { sdp, type, session_id } = await res.json();
      sessionIdRef.current = session_id;

      // 6. Set server's answer
      await pc.setRemoteDescription({ sdp, type });

      // 7. Send ICE candidates to server
      pc.onicecandidate = async (event) => {
        if (event.candidate && session_id) {
          await fetch(ICE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id,
              candidate: event.candidate,
            }),
          }).catch(() => {});
        }
      };

      pc.onconnectionstatechange = () => {
        const state = pc.connectionState;
        if (state === "connected") {
          setStatus(STATUS.CONNECTED);
          setTranscript((t) => [...t, { role: "system", text: "Voice session started. Speak now." }]);
        } else if (state === "disconnected" || state === "failed" || state === "closed") {
          setStatus(STATUS.DISCONNECTED);
        }
      };

    } catch (err) {
      console.error(err);
      setError(err.message || "Could not connect to voice bot.");
      setStatus(STATUS.ERROR);
    }
  }

  function disconnect() {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.srcObject = null;
    }
    sessionIdRef.current = null;
    setStatus(STATUS.IDLE);
  }

  const isActive = status === STATUS.CONNECTED ||
                   status === STATUS.SPEAKING   ||
                   status === STATUS.LISTENING;

  return (
    <div className="voice-page">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-brand">
          <div className="chat-avatar voice-avatar">🎙</div>
          <div>
            <p className="chat-bot-name">InsureFlow Voice</p>
            <p className="chat-status">
              <span className={`chat-dot ${isActive ? "chat-dot-active" : ""}`} />
              {STATUS_LABEL[status]}
            </p>
          </div>
        </div>
        <Link to="/" className="chat-icon-btn" title="Go home">✕</Link>
      </header>

      {/* Orb animation */}
      <div className="voice-center">
        <div className={`voice-orb ${isActive ? "voice-orb-active" : ""} ${status === STATUS.CONNECTING ? "voice-orb-pulse" : ""}`}>
          <div className="voice-orb-ring" />
          <div className="voice-orb-ring voice-orb-ring-2" />
          <span className="voice-orb-icon">
            {status === STATUS.CONNECTING ? "⟳" : isActive ? "🎙" : "🎙"}
          </span>
        </div>

        <p className="voice-hint">
          {status === STATUS.IDLE
            ? "Press Connect to start speaking with InsureFlow AI"
            : status === STATUS.CONNECTING
            ? "Setting up secure audio channel…"
            : status === STATUS.CONNECTED
            ? "Speak naturally — ask about insurance plans, pricing, or your policy"
            : status === STATUS.ERROR
            ? "Could not connect. Is the bot server running on port 8002?"
            : "Session ended"}
        </p>

        {error && (
          <div className="alert-box alert-error voice-error">⚠ {error}</div>
        )}

        {/* Control buttons */}
        <div className="voice-controls">
          {!isActive && status !== STATUS.CONNECTING ? (
            <button id="voice-connect-btn" className="primary-button voice-btn" onClick={connect}>
              Connect
            </button>
          ) : (
            <button id="voice-disconnect-btn" className="secondary-button voice-btn" onClick={disconnect}>
              End Call
            </button>
          )}
        </div>
      </div>

      {/* Transcript */}
      {transcript.length > 0 && (
        <div className="voice-transcript">
          <p className="voice-transcript-label">Session log</p>
          {transcript.map((t, i) => (
            <p key={i} className={`voice-transcript-line ${t.role === "system" ? "voice-transcript-system" : ""}`}>
              {t.text}
            </p>
          ))}
        </div>
      )}

      {/* Hidden audio element for bot voice output */}
      <audio ref={audioRef} autoPlay playsInline style={{ display: "none" }} />
    </div>
  );
}

export default VoiceBotPage;
