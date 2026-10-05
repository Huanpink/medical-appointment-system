from pydantic import BaseModel, Field
class AppointmentCreate(BaseModel): doctor_id:int; appointment_date:str; start_time:str; reason:str=Field(min_length=3,max_length=500)
class AppointmentOut(BaseModel):
    id:int; patient_id:int; doctor_id:int; doctor_name:str; appointment_date:str; start_time:str; end_time:str; reason:str; status:str; visit_type:str; specialty_name:str|None=None; patient_name:str|None=None
class RescheduleIn(BaseModel): appointment_date:str; start_time:str
class MedicalResultIn(BaseModel): diagnosis:str=Field(min_length=2); notes:str=""; prescription:str=""
class WalkInIn(BaseModel): patient_id:int; doctor_id:int; reason:str=Field(min_length=3)
class QueueOut(BaseModel): id:int; appointment_id:int; queue_no:int; patient_name:str; doctor_name:str; appointment_date:str; start_time:str; priority:int; status:str; called_at:str|None=None
