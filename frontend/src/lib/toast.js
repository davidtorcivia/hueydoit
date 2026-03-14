let _listeners = [];
let _id = 0;

export function toast(message, type = 'info', duration = 3000) {
  const t = { id: ++_id, message, type, duration };
  _listeners.forEach(fn => fn(t));
  return t.id;
}

toast.success = (msg, duration) => toast(msg, 'success', duration);
toast.error = (msg, duration) => toast(msg, 'error', duration ?? 5000);
toast.warning = (msg, duration) => toast(msg, 'warning', duration);
toast.info = (msg, duration) => toast(msg, 'info', duration);

export function onToast(fn) {
  _listeners.push(fn);
  return () => { _listeners = _listeners.filter(l => l !== fn); };
}
