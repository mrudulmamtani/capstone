import { useEffect, useRef, useState } from "react";

const wsBase = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export function useLiveSession(sessionId) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("disconnected");
  const ws = useRef(null);

  useEffect(() => {
    if (!sessionId) return;
    const url = `${wsBase}/api/monitor/ws/${sessionId}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("error");
    socket.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        setEvents((prev) => [...prev.slice(-199), payload]);
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => socket.close();
  }, [sessionId]);

  return { events, status };
}
