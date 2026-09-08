import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / '_stubs'))
DB = Path(__file__).parent / 'smoke.db'
if DB.exists(): DB.unlink()
os.environ['DATABASE_URL'] = f'sqlite:///{DB}'
os.environ['JWT_SECRET'] = 'test-secret'
os.environ['CORS_ORIGINS'] = 'http://localhost:5173'

from fastapi.testclient import TestClient
from app.main import app


def login(email):
    r = client.post('/api/auth/login', json={'email': email, 'password': '123456'})
    assert r.status_code == 200, r.text
    return {'Authorization': f"Bearer {r.json()['access_token']}"}

with TestClient(app) as client:
    def test_health_and_login():
        r = client.get('/healthz'); assert r.status_code == 200
        h = login('patient@medschedule.local')
        me = client.get('/api/auth/me', headers=h)
        assert me.status_code == 200 and me.json()['role'] == 'PATIENT'

    def test_patient_booking_and_reschedule_cancel():
        h = login('patient@medschedule.local')
        doctors = client.get('/api/doctors'); assert doctors.status_code == 200 and doctors.json()
        doctor_id = doctors.json()[0]['id']
        slots = client.get(f'/api/doctors/{doctor_id}/available-slots', params={'date':'2030-01-07'})
        assert slots.status_code == 200 and slots.json()
        start = slots.json()[0]['start_time']
        services = client.get('/api/services', params={'specialtyId': doctors.json()[0]['specialty_id']}); assert services.status_code == 200 and services.json()
        service_id = services.json()[0]['id']
        create = client.post('/api/appointments', headers=h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':'2030-01-07','start_time':start,'reason':'Khám định kỳ','payment_method':'OFFLINE'})
        assert create.status_code == 200, create.text
        aid = create.json()['id']
        dup = client.post('/api/appointments', headers=h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':'2030-01-07','start_time':start,'reason':'Lịch trùng','payment_method':'OFFLINE'})
        assert dup.status_code == 409
        detail = client.get(f'/api/appointments/{aid}', headers=h)
        assert detail.status_code == 200 and detail.json()['patient_phone'] == '0900000005'
        later = next(x for x in slots.json() if x['start_time'] != start)['start_time']
        res = client.patch(f'/api/appointments/{aid}/reschedule', headers=h, json={'appointment_date':'2030-01-07','start_time':later})
        assert res.status_code == 200, res.text
        cancel = client.patch(f'/api/appointments/{aid}/cancel', headers=h)
        assert cancel.status_code == 200
        free = client.post('/api/appointments', headers=h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':'2030-01-07','start_time':later,'reason':'Đặt lại sau hủy','payment_method':'OFFLINE'})
        assert free.status_code == 200

    def test_reception_checkin_queue_walkin_and_no_show():
        from datetime import date
        patient_h = login('patient@medschedule.local')
        doctors = client.get('/api/doctors').json(); doctor_id = doctors[0]['id']
        today_str = date.today().isoformat()
        slots = client.get(f'/api/doctors/{doctor_id}/available-slots', params={'date':today_str}).json()
        assert slots, 'Need at least one future slot today for queue smoke test'
        service_id = client.get('/api/services', params={'specialtyId': doctors[0]['specialty_id']}).json()[0]['id']
        aid = client.post('/api/appointments', headers=patient_h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':today_str,'start_time':slots[0]['start_time'],'reason':'Khám','payment_method':'OFFLINE'}).json()['id']
        rec_h = login('reception@medschedule.local')
        today = client.get('/api/appointments', headers=rec_h, params={'date':today_str})
        assert today.status_code == 200 and any(x['id'] == aid for x in today.json())
        assert today.json()[0]['appointment_code'].startswith('AP-')
        search = client.get('/api/patients/search', headers=rec_h, params={'q':'0900000005'})
        assert search.status_code == 200 and search.json()[0]['patient_code'].startswith('BN-')
        check = client.patch(f'/api/appointments/{aid}/check-in', headers=rec_h)
        assert check.status_code == 200 and check.json()['status'] == 'WAITING'
        q = client.get('/api/queue', headers=rec_h); assert q.status_code == 200 and q.json()
        qid = next(x['id'] for x in q.json() if x['appointment_id'] == aid)
        called = client.patch(f'/api/queue/{qid}/call', headers=rec_h)
        assert called.status_code == 200 and called.json()['queue']['called_at']
        walk = client.post('/api/walk-ins', headers=rec_h, json={'patient_id':1,'doctor_id':doctor_id,'reason':'Đau đầu'})
        assert walk.status_code == 200 and walk.json()['visit_type'] == 'WALK_IN' and walk.json()['status'] == 'WAITING'
        # Past appointment can be marked no-show after the 15-minute threshold.
        old = client.post('/api/appointments', headers=patient_h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':'2020-01-09','start_time':'08:00','reason':'Không đến','payment_method':'QR'})
        assert old.status_code == 200
        old_id = old.json()['id']
        ns = client.patch(f'/api/appointments/{old_id}/no-show', headers=rec_h)
        assert ns.status_code == 200

    def test_doctor_examination_and_result():
        patient_h = login('patient@medschedule.local'); doctor_id = client.get('/api/doctors').json()[0]['id']
        future = client.get(f'/api/doctors/{doctor_id}/available-slots', params={'date':'2030-01-10'}).json()[0]['start_time']
        service_id = client.get('/api/services', params={'specialtyId': client.get('/api/doctors').json()[0]['specialty_id']}).json()[0]['id']
        aid = client.post('/api/appointments', headers=patient_h, json={'doctor_id':doctor_id,'service_id':service_id,'appointment_date':'2030-01-10','start_time':future,'reason':'Khám chuyên khoa','payment_method':'OFFLINE'}).json()['id']
        rec_h = login('reception@medschedule.local'); client.patch(f'/api/appointments/{aid}/check-in', headers=rec_h)
        doc_h = login('doctor@medschedule.local')
        forbidden = client.patch(f'/api/appointments/{aid}/start', headers=rec_h); assert forbidden.status_code == 403
        start = client.patch(f'/api/appointments/{aid}/start', headers=doc_h); assert start.status_code == 200
        result = client.post(f'/api/appointments/{aid}/medical-result', headers=doc_h, json={'diagnosis':'Theo dõi','notes':'Ổn định','prescription':'Nghỉ ngơi'})
        assert result.status_code == 200
        complete = client.patch(f'/api/appointments/{aid}/complete', headers=doc_h); assert complete.status_code == 200
        mine = client.get('/api/patients/me/appointments', headers=patient_h).json()
        row = next(x for x in mine if x['id'] == aid)
        assert row['status'] == 'COMPLETED' and row['diagnosis'] == 'Theo dõi'

    def test_payment_qr_and_refund_flow():
        patient_h = login('patient@medschedule.local')
        doctors = client.get('/api/doctors').json(); doctor_id = doctors[0]['id']; specialty_id = doctors[0]['specialty_id']
        service = client.get('/api/services', params={'specialtyId':specialty_id}).json()[0]
        slots = client.get(f'/api/doctors/{doctor_id}/available-slots', params={'date':'2030-01-15'}).json(); assert slots
        create=client.post('/api/appointments',headers=patient_h,json={'doctor_id':doctor_id,'service_id':service['id'],'appointment_date':'2030-01-15','start_time':slots[0]['start_time'],'reason':'Thanh toán QR','payment_method':'QR'})
        assert create.status_code==200, create.text
        row=create.json(); assert row['payment_status']=='PENDING' and row['service_price']==service['price'] and row['qr_image'].startswith('data:image/png;base64,')
        p=client.get(f"/api/payments/{row['id']}",headers=patient_h); assert p.status_code==200 and p.json()['amount']==service['price']
        paid=client.post(f"/api/payments/{row['id']}/confirm-demo",headers=patient_h); assert paid.status_code==200 and paid.json()['status']=='PAID'
        cancel=client.patch(f"/api/appointments/{row['id']}/cancel",headers=patient_h); assert cancel.status_code==200
        p2=client.get(f"/api/payments/{row['id']}",headers=patient_h); assert p2.status_code==200 and p2.json()['status']=='REFUND_PENDING'
        rec_h=login('reception@medschedule.local')
        refunded=client.post(f"/api/payments/{row['id']}/refund",headers=rec_h); assert refunded.status_code==200 and refunded.json()['status']=='REFUNDED'

    def test_admin_management_patient_doctor_service_and_schedule():
        admin_h = login('admin@medschedule.local')
        patients = client.get('/api/admin/patients', headers=admin_h, params={'q':'0900000005'})
        assert patients.status_code == 200 and patients.json()[0]['patient_code'].startswith('BN-')
        pat = patients.json()[0]
        updated = dict(pat, full_name='Nguyễn Hồng Huân Admin', email=pat['email'], phone=pat['phone'], date_of_birth='2000-01-01', gender='Nam', address='TP HCM', emergency_contact='0900000006')
        up = client.put(f"/api/admin/patients/{pat['patient_id']}", headers=admin_h, json=updated)
        assert up.status_code == 200
        doctors = client.get('/api/admin/doctors', headers=admin_h); assert doctors.status_code == 200 and doctors.json()
        specs = client.get('/api/specialties').json()
        doc = doctors.json()[0]
        dupdoc = client.put(f"/api/admin/doctors/{doc['doctor_id']}", headers=admin_h, json={**doc, 'specialty_id': specs[0]['id'], 'doctor_id': doc['doctor_id'], 'user_id': doc['user_id'], 'email': 'doctor.updated@gmail.com'})
        assert dupdoc.status_code == 200, dupdoc.text
        assert dupdoc.json()['email'] == 'doctor.updated@gmail.com'
        doctors_after = client.get('/api/admin/doctors', headers=admin_h).json()
        updated_doc = next(x for x in doctors_after if x['doctor_id'] == doc['doctor_id'])
        assert updated_doc['email'] == 'doctor.updated@gmail.com'
        services = client.get('/api/admin/services', headers=admin_h); assert services.status_code == 200 and services.json()
        svc = services.json()[0]
        us = client.put(f"/api/admin/services/{svc['id']}", headers=admin_h, json={**svc})
        assert us.status_code == 200
        sched = client.get(f"/api/doctors/{doc['doctor_id']}/schedules", headers=admin_h); assert sched.status_code == 200 and sched.json()
