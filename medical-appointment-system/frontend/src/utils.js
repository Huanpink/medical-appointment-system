export function getErrorMessage(error, fallback = 'Có lỗi xảy ra. Vui lòng thử lại.') {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => item?.msg || item?.message || item)
      .filter(Boolean)
      .map(String);
    if (messages.length) return messages.join(' · ');
  }
  if (detail && typeof detail === 'object') {
    if (detail.msg) return String(detail.msg);
    if (detail.message) return String(detail.message);
    try { return JSON.stringify(detail); } catch { return fallback; }
  }
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (typeof error?.message === 'string' && error.message.trim()) return error.message;
  return fallback;
}
