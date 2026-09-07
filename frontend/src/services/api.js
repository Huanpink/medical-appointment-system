import axios from 'axios';

const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api',headers:{'Content-Type':'application/json'}});
api.interceptors.request.use(config=>{const token=localStorage.getItem('med_token');if(token)config.headers.Authorization=`Bearer ${token}`;return config});
api.interceptors.response.use(r=>r,e=>{if(e.response?.status===401){localStorage.removeItem('med_token');localStorage.removeItem('med_user');if(location.pathname!=='/login')location.href='/login'}return Promise.reject(e)});

export const authApi={login:d=>api.post('/auth/login',d),register:d=>api.post('/auth/register',d),me:()=>api.get('/auth/me'),changePassword:d=>api.patch('/auth/password',d)};
export const masterApi={specialties:()=>api.get('/specialties'),doctors:sid=>api.get('/doctors',{params:sid?{specialtyId:sid}:undefined}),doctor:id=>api.get(`/doctors/${id}`),profile:id=>api.get(`/patients/${id}`),updateProfile:(id,d)=>api.put(`/patients/${id}`,d),searchPatients:q=>api.get('/patients/search',{params:{q}})};
export const bookingApi={slots:(id,date)=>api.get(`/doctors/${id}/available-slots`,{params:{date}}),create:d=>api.post('/appointments',d),mine:()=>api.get('/patients/me/appointments'),get:id=>api.get(`/appointments/${id}`),cancel:id=>api.patch(`/appointments/${id}/cancel`),reschedule:(id,d)=>api.patch(`/appointments/${id}/reschedule`,d)};
export const receptionApi={appointments:date=>api.get('/appointments',{params:{date}}),checkIn:id=>api.patch(`/appointments/${id}/check-in`),noShow:id=>api.patch(`/appointments/${id}/no-show`),walkIn:d=>api.post('/walk-ins',d),queue:doctorId=>api.get('/queue',{params:doctorId?{doctorId}:undefined}),addQueue:appointment_id=>api.post('/queue',{appointment_id}),call:id=>api.patch(`/queue/${id}/call`)};
export const doctorApi={mine:()=>api.get('/doctors/me/appointments'),schedules:id=>api.get(`/doctors/${id}/schedules`),addSchedule:(id,d)=>api.post(`/doctors/${id}/schedules`,d),updateSchedule:(id,sid,d)=>api.put(`/doctors/${id}/schedules/${sid}`,d),daysOff:id=>api.get(`/doctors/${id}/days-off`),addDayOff:(id,d)=>api.post(`/doctors/${id}/days-off`,d),start:id=>api.patch(`/appointments/${id}/start`),result:(id,d)=>api.post(`/appointments/${id}/medical-result`,d),complete:id=>api.patch(`/appointments/${id}/complete`),queue:id=>api.get('/queue',{params:{doctorId:id}})};
export const adminApi={dashboard:()=>api.get('/admin/dashboard')};
export default api;
