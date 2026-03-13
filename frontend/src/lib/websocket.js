let socket = null;
let reconnectDelay = 1000;
let listeners = [];

export function addWSListener(fn) {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter(l => l !== fn);
  };
}

function notify(event, data) {
  for (const fn of listeners) {
    try { fn(event, data); } catch (e) { console.error('WS listener error:', e); }
  }
}

export function connectWS() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${location.host}/api/stream`;

  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log('WebSocket connected');
    reconnectDelay = 1000;
    notify('_connected', {});
  };

  socket.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data);
      notify(msg.event, msg.data);
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket closed, reconnecting in', reconnectDelay, 'ms');
    notify('_disconnected', {});
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      connectWS();
    }, reconnectDelay);
  };

  socket.onerror = (err) => {
    console.error('WebSocket error:', err);
    socket.close();
  };
}

export function disconnectWS() {
  if (socket) {
    socket.close();
    socket = null;
  }
}
