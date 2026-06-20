import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

const BOT_BASE_URL = import.meta.env.VITE_BOT_BASE_URL ?? "http://localhost:8002";
const OFFER_URL = `${BOT_BASE_URL}/voice/offer`;
const ICE_URL = `${BOT_BASE_URL}/voice/ice`;

const STATUS = {
  IDLE: "idle",
  CONNECTING: "connecting",
  CONNECTED: "connected",
  SPEAKING: "speaking",
  LISTENING: "listening",
  DISCONNECTED: "disconnected",
  ERROR: "error",
};

const STATUS_LABEL = {
  [STATUS.IDLE]: "Ready to connect",
  [STATUS.CONNECTING]: "Connecting...",
  [STATUS.CONNECTED]: "Connected - speak to InsureFlow",
  [STATUS.SPEAKING]: "InsureFlow is speaking...",
  [STATUS.LISTENING]: "Listening...",
  [STATUS.DISCONNECTED]: "Disconnected",
  [STATUS.ERROR]: "Connection failed",
};

function formatDuration(seconds) {
  const safeSeconds = Math.max(0, Number(seconds || 0));
  const minutes = Math.floor(safeSeconds / 60);
  const remainingSeconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function VoiceBotPage() {
  const [status, setStatus] = useState(STATUS.IDLE);
  const [transcript, setTranscript] = useState([]);
  const [error, setError] = useState(null);
  const [callHistory, setCallHistory] = useState([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const pcRef = useRef(null);
  const sessionIdRef = useRef(null);
  const audioRef = useRef(null);
  const startTimeRef = useRef(null);
  const tickerRef = useRef(null);

  useEffect(() => () => disconnect(), []);

  useEffect(() => {
    if (status === STATUS.CONNECTED || status === STATUS.LISTENING || status === STATUS.SPEAKING) {
      tickerRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          const seconds = Math.floor((Date.now() - startTimeRef.current) / 1000);
          setElapsedSeconds(seconds);
        }
      }, 1000);
      return () => {
        window.clearInterval(tickerRef.current);
      };
    }

    window.clearInterval(tickerRef.current);
    return undefined;
  }, [status]);

  const isActive =
    status === STATUS.CONNECTED ||
    status === STATUS.SPEAKING ||
    status === STATUS.LISTENING;

  const latestCall = useMemo(() => callHistory[0] || null, [callHistory]);

  async function connect() {
    setError(null);
    setStatus(STATUS.CONNECTING);
    setTranscript([]);
    setElapsedSeconds(0);
    startTimeRef.current = Date.now();

    try {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      pc.ontrack = (event) => {
        if (audioRef.current && event.streams[0]) {
          audioRef.current.srcObject = event.streams[0];
          setStatus(STATUS.SPEAKING);
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const response = await fetch(OFFER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
      });
      if (!response.ok) {
        throw new Error(`Offer failed: ${response.status}`);
      }

      const { sdp, type, session_id } = await response.json();
      sessionIdRef.current = session_id;

      await pc.setRemoteDescription({ sdp, type });

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
          setTranscript((currentValue) => [
            ...currentValue,
            { role: "system", text: "Voice session started. Speak now." },
          ]);
        } else if (state === "disconnected" || state === "failed" || state === "closed") {
          setStatus(STATUS.DISCONNECTED);
        }
      };
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not connect to voice bot.");
      setStatus(STATUS.ERROR);
      startTimeRef.current = null;
    }
  }

  function disconnect() {
    const finishedDuration = startTimeRef.current
      ? Math.floor((Date.now() - startTimeRef.current) / 1000)
      : elapsedSeconds;

    if ((isActive || transcript.length > 0) && finishedDuration >= 0) {
      setCallHistory((currentValue) => [
        {
          id: Date.now(),
          startedAt: new Date().toLocaleString(),
          durationSeconds: finishedDuration,
          status: status === STATUS.ERROR ? "Failed" : "Completed",
          transcriptCount: transcript.length,
        },
        ...currentValue,
      ]);
    }

    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.srcObject = null;
    }

    window.clearInterval(tickerRef.current);
    sessionIdRef.current = null;
    startTimeRef.current = null;
    setElapsedSeconds(0);
    setStatus(STATUS.IDLE);
  }

  return (
    <div className="voice-page">
      <section className="voice-workspace">
        <header className="chat-header">
          <div className="chat-header-brand">
            <div className="chat-avatar voice-avatar">VB</div>
            <div>
              <p className="chat-bot-name">InsureFlow Voice Bot</p>
              <p className="chat-status">
                <span className={`chat-dot ${isActive ? "chat-dot-active" : ""}`} />
                {STATUS_LABEL[status]}
              </p>
            </div>
          </div>
          <div className="chat-header-actions">
            <Link to="/" className="chat-icon-btn" title="Go home">
              Home
            </Link>
          </div>
        </header>

        <div className="voice-dashboard-grid">
          <section className="voice-main-card">
            <div className="voice-center">
              <div
                className={`voice-orb ${isActive ? "voice-orb-active" : ""} ${
                  status === STATUS.CONNECTING ? "voice-orb-pulse" : ""
                }`}
              >
                <div className="voice-orb-ring" />
                <div className="voice-orb-ring voice-orb-ring-2" />
                <span className="voice-orb-icon">VB</span>
              </div>

              <div className="voice-call-meta">
                <p className="eyebrow-text">Live call status</p>
                <h2>{STATUS_LABEL[status]}</h2>
                <p className="voice-hint">
                  {status === STATUS.IDLE
                    ? "Press Connect to start speaking with the InsureFlow voice assistant."
                    : status === STATUS.CONNECTING
                    ? "Setting up a secure audio channel..."
                    : status === STATUS.CONNECTED || status === STATUS.SPEAKING
                    ? "Speak naturally about plans, policies, prices, or your insurance journey."
                    : status === STATUS.ERROR
                    ? "Could not connect. Make sure the bot server is running on port 8002."
                    : "Session ended"}
                </p>
              </div>

              <div className="voice-stats-row">
                <div className="mini-card">
                  <p className="eyebrow-text">Duration</p>
                  <h4>{formatDuration(elapsedSeconds)}</h4>
                </div>
                <div className="mini-card">
                  <p className="eyebrow-text">Current session</p>
                  <h4>{sessionIdRef.current ? "Active" : "Not connected"}</h4>
                </div>
                <div className="mini-card">
                  <p className="eyebrow-text">History entries</p>
                  <h4>{callHistory.length}</h4>
                </div>
              </div>

              {error ? <div className="alert-box alert-error voice-error">{error}</div> : null}

              <div className="voice-controls">
                {!isActive && status !== STATUS.CONNECTING ? (
                  <button className="primary-button voice-btn" onClick={connect}>
                    Connect
                  </button>
                ) : (
                  <button className="secondary-button voice-btn" onClick={disconnect}>
                    End call
                  </button>
                )}
              </div>
            </div>
          </section>

          <aside className="voice-side-panel">
            <div className="mini-card">
              <p className="eyebrow-text">Latest session</p>
              {latestCall ? (
                <>
                  <p>
                    <strong>Started:</strong> {latestCall.startedAt}
                  </p>
                  <p>
                    <strong>Duration:</strong> {formatDuration(latestCall.durationSeconds)}
                  </p>
                  <p>
                    <strong>Status:</strong> {latestCall.status}
                  </p>
                </>
              ) : (
                <p>No previous session recorded yet in this browser view.</p>
              )}
            </div>

            <div className="mini-card">
              <p className="eyebrow-text">Call history</p>
              {callHistory.length === 0 ? (
                <p>No calls yet. Start a voice session to begin tracking duration and status.</p>
              ) : (
                <div className="voice-history-list">
                  {callHistory.map((item) => (
                    <div key={item.id} className="voice-history-item">
                      <strong>{item.startedAt}</strong>
                      <p>
                        Duration {formatDuration(item.durationSeconds)} - {item.status}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>

        {transcript.length > 0 ? (
          <div className="voice-transcript">
            <p className="voice-transcript-label">Session log</p>
            {transcript.map((item, index) => (
              <p
                key={`${item.role}-${index}`}
                className={`voice-transcript-line ${
                  item.role === "system" ? "voice-transcript-system" : ""
                }`}
              >
                {item.text}
              </p>
            ))}
          </div>
        ) : null}

        <audio ref={audioRef} autoPlay playsInline style={{ display: "none" }} />
      </section>
    </div>
  );
}

export default VoiceBotPage;
