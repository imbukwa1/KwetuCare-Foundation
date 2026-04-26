import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL, getStoredAccessToken } from "./api";

function buildWebSocketUrl(websocketPath) {
  const configuredUrl = process.env.REACT_APP_WS_URL;
  if (configuredUrl) {
    return configuredUrl;
  }

  const apiBase =
    API_BASE_URL.startsWith("http")
      ? API_BASE_URL
      : `${window.location.origin}${API_BASE_URL.startsWith("/") ? "" : "/"}${API_BASE_URL}`;

  const origin = apiBase.replace(/\/api\/?$/, "");
  return `${origin.replace(/^http/, "ws")}${websocketPath}`;
}

function getBackoffInterval(baseInterval, failureCount) {
  if (failureCount >= 3) {
    return 10000;
  }
  if (failureCount >= 1) {
    return 6000;
  }
  return baseInterval;
}

function parseSocketMessage(rawMessage) {
  if (!rawMessage) {
    return null;
  }

  if (typeof rawMessage === "object") {
    return rawMessage;
  }

  try {
    return JSON.parse(rawMessage);
  } catch {
    return { type: null, raw: rawMessage };
  }
}

export default function useHybridDataSync({
  fetcher,
  onData,
  onError,
  enabled = true,
  intervalMs = 4000,
  websocketPath = "/ws/updates/",
  reconnectDelayMs = 3000,
  relevantEventTypes = [],
  shouldRefreshMessage,
}) {
  const [isTabActive, setIsTabActive] = useState(
    typeof document === "undefined" ? true : document.visibilityState !== "hidden"
  );
  const [lastUpdated, setLastUpdated] = useState(null);
  const [currentIntervalMs, setCurrentIntervalMs] = useState(intervalMs);
  const intervalRef = useRef(null);
  const websocketRef = useRef(null);
  const reconnectRef = useRef(null);
  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);
  const consecutiveFailuresRef = useRef(0);
  const fetcherRef = useRef(fetcher);
  const onDataRef = useRef(onData);
  const onErrorRef = useRef(onError);
  const shouldRefreshMessageRef = useRef(shouldRefreshMessage);
  const relevantEventTypesRef = useRef(relevantEventTypes);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    onDataRef.current = onData;
  }, [onData]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    shouldRefreshMessageRef.current = shouldRefreshMessage;
  }, [shouldRefreshMessage]);

  useEffect(() => {
    relevantEventTypesRef.current = relevantEventTypes;
  }, [relevantEventTypes]);

  useEffect(() => {
    setCurrentIntervalMs(intervalMs);
  }, [intervalMs]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const stopWebSocket = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }

    if (websocketRef.current) {
      websocketRef.current.onopen = null;
      websocketRef.current.onmessage = null;
      websocketRef.current.onerror = null;
      websocketRef.current.onclose = null;
      websocketRef.current.close();
      websocketRef.current = null;
    }
  }, []);

  const scheduleReconnect = useCallback(
    (connect) => {
      if (reconnectRef.current || !mountedRef.current) {
        return;
      }
      reconnectRef.current = setTimeout(() => {
        reconnectRef.current = null;
        connect();
      }, reconnectDelayMs);
    },
    [reconnectDelayMs]
  );

  const refresh = useCallback(
    async ({ showLoading = false, source = "manual" } = {}) => {
      if (!enabled || inFlightRef.current) {
        return null;
      }

      inFlightRef.current = true;
      try {
        const data = await fetcherRef.current({ showLoading, source });
        consecutiveFailuresRef.current = 0;
        setCurrentIntervalMs(intervalMs);
        setLastUpdated(new Date());
        if (mountedRef.current && onDataRef.current) {
          onDataRef.current(data, { showLoading, source });
        }
        return data;
      } catch (error) {
        consecutiveFailuresRef.current += 1;
        setCurrentIntervalMs(
          getBackoffInterval(intervalMs, consecutiveFailuresRef.current)
        );
        if (mountedRef.current && onErrorRef.current) {
          onErrorRef.current(error, { showLoading, source });
        }
        throw error;
      } finally {
        inFlightRef.current = false;
      }
    },
    [enabled, intervalMs]
  );

  useEffect(() => {
    const handleFocus = () => setIsTabActive(true);
    const handleBlur = () => setIsTabActive(false);
    const handleVisibilityChange = () => setIsTabActive(document.visibilityState !== "hidden");

    window.addEventListener("focus", handleFocus);
    window.addEventListener("blur", handleBlur);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("blur", handleBlur);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    stopPolling();

    if (!enabled || !isTabActive) {
      return undefined;
    }

    intervalRef.current = setInterval(() => {
      refresh({ source: "poll" }).catch(() => {});
    }, currentIntervalMs);

    return stopPolling;
  }, [currentIntervalMs, enabled, isTabActive, refresh, stopPolling]);

  useEffect(() => {
    stopWebSocket();

    if (!enabled || !isTabActive) {
      return undefined;
    }

    let isCancelled = false;

    const connect = () => {
      if (isCancelled || !mountedRef.current || !isTabActive) {
        return;
      }

      try {
        const socketUrl = new URL(buildWebSocketUrl(websocketPath));
        const token = getStoredAccessToken();
        if (token) {
          socketUrl.searchParams.set("token", token);
        }

        const socket = new WebSocket(socketUrl.toString());
        websocketRef.current = socket;

        socket.onopen = () => {
          if (reconnectRef.current) {
            clearTimeout(reconnectRef.current);
            reconnectRef.current = null;
          }
        };

        socket.onmessage = (event) => {
          const parsedMessage = parseSocketMessage(event.data);
          const eventType = parsedMessage?.type || parsedMessage?.event || null;
          const explicitDecision = shouldRefreshMessageRef.current
            ? shouldRefreshMessageRef.current(parsedMessage)
            : null;
          const isRelevant =
            explicitDecision !== null && explicitDecision !== undefined
              ? explicitDecision
              : relevantEventTypesRef.current.length === 0 || !eventType
                ? true
                : relevantEventTypesRef.current.includes(eventType);

          if (isRelevant) {
            refresh({ source: `websocket:${eventType || "message"}` }).catch(() => {});
          }
        };

        socket.onerror = () => {
          if (websocketRef.current === socket) {
            socket.close();
          }
        };

        socket.onclose = () => {
          if (websocketRef.current === socket) {
            websocketRef.current = null;
          }
          if (!isCancelled && isTabActive) {
            scheduleReconnect(connect);
          }
        };
      } catch {
        scheduleReconnect(connect);
      }
    };

    connect();

    return () => {
      isCancelled = true;
      stopWebSocket();
    };
  }, [enabled, isTabActive, reconnectDelayMs, refresh, scheduleReconnect, stopWebSocket, websocketPath]);

  return {
    currentIntervalMs,
    isTabActive,
    lastUpdated,
    refresh,
  };
}
