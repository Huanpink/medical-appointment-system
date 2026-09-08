import axios from 'axios';

export function getApiErrorMessage(error, fallback = 'Có lỗi xảy ra. Vui lòng thử lại.') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map(item => typeof item === 'string' ? item : item?.msg).filter(Boolean);
    if (messages.length) return messages.join(', ');
  }
  if (detail && typeof detail === 'object' && typeof detail.msg === 'string') return detail.msg;
  return fallback;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});
api.interceptors.request.use(config => {
  const token = localStorage.getItem('med_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(r => r, e => {
  if (e.response?.status === 401) {
    localStorage.removeItem('med_token');
    localStorage.removeItem('med_user');
    if (location.hash !== '#/login') location.hash = '#/login';
  }
  return Promise.reject(e);
});

export const authApi = {
  login: d => api.post('/auth/login', d), register: d => api.post('/auth/register', d), me: () => api.get('/auth/me'), changePassword: d => api.patch('/auth/password', d),
};
export const masterApi = {
  specialties: () => api.get('/specialties'), services: sid => api.get('/services', { params: sid ? { specialtyId: sid } : undefined }), doctors: sid => api.get('/doctors', { params: sid ? { specialtyId: sid } : undefined }), doctor: id => api.get(`/doctors/${id}`),
  profile: id => api.get(`/patients/${id}`), updateProfile: (id, d) => api.put(`/patients/${id}`, d), searchPatients: q => api.get('/patients/search', { params: { q } }),
  createReceptionPatient: d => api.post('/reception-patients', d),
};
export const paymentApi = { get: id => api.get(`/payments/${id}`), confirmDemo: id => api.post(`/payments/${id}/confirm-demo`), payLater: id => api.post(`/payments/${id}/pay-later`), refund: id => api.post(`/payments/${id}/refund`) };
export const bookingApi = {
  slots: (id, date) => api.get(`/doctors/${id}/available-slots`, { params: { date } }), create: d => api.post('/appointments', d), mine: () => api.get('/patients/me/appointments'),
  get: id => api.get(`/appointments/${id}`), cancel: id => api.patch(`/appointments/${id}/cancel`), reschedule: (id, d) => api.patch(`/appointments/${id}/reschedule`, d),
};
export const receptionApi = {
  appointments: date => api.get('/appointments', { params: { date } }), refundRequests: () => api.get('/refund-requests'), checkIn: id => api.patch(`/appointments/${id}/check-in`), noShow: id => api.patch(`/appointments/${id}/no-show`),
  walkIn: d => api.post('/walk-ins', d), queue: doctorId => api.get('/queue', { params: doctorId ? { doctorId } : undefined }), addQueue: appointment_id => api.post('/queue', { appointment_id }), call: id => api.patch(`/queue/${id}/call`),
};
export const doctorApi = {
  mine: () => api.get('/doctors/me/appointments'), schedules: id => api.get(`/doctors/${id}/schedules`), addSchedule: (id, d) => api.post(`/doctors/${id}/schedules`, d),
  updateSchedule: (id, sid, d) => api.put(`/doctors/${id}/schedules/${sid}`, d), daysOff: id => api.get(`/doctors/${id}/days-off`), addDayOff: (id, d) => api.post(`/doctors/${id}/days-off`, d),
  start: id => api.patch(`/appointments/${id}/start`), result: (id, d) => api.post(`/appointments/${id}/medical-result`, d), complete: id => api.patch(`/appointments/${id}/complete`), queue: id => api.get('/queue', { params: { doctorId: id } }),
};
export const adminApi = {
  dashboard: () => api.get('/admin/dashboard'),
  patients: q => api.get('/admin/patients', { params: q ? { q } : undefined }),
  updatePatient: (id, d) => api.put(`/admin/patients/${id}`, d),
  specialties: () => api.get('/admin/specialties'),
  createSpecialty: d => api.post('/admin/specialties', d),
  doctors: () => api.get('/admin/doctors'),
  createDoctor: d => api.post('/admin/doctors', d),
  updateDoctor: (id, d) => api.put(`/admin/doctors/${id}`, d),
  services: () => api.get('/admin/services'),
  createService: d => api.post('/admin/services', d),
  updateService: (id, d) => api.put(`/admin/services/${id}`, d),
};
export default api;
