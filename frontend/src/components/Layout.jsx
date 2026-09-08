import {NavLink, useNavigate} from 'react-router-dom';
import {CalendarDays, ClipboardList, Stethoscope, LayoutDashboard, LogOut, UserRound, Clock3, Search, UserPlus, BriefcaseMedical, WalletCards} from 'lucide-react';
import {useAuth} from '../context/AuthContext';

const menus={
  PATIENT:[['/patient',LayoutDashboard,'Tổng quan'],['/patient/book',CalendarDays,'Đặt lịch'],['/patient/appointments',ClipboardList,'Lịch của tôi'],['/patient/payments',WalletCards,'Thanh toán'],['/patient/profile',UserRound,'Hồ sơ']],
  RECEPTIONIST:[['/reception',LayoutDashboard,'Tiếp nhận bệnh nhân'],['/reception/queue',Clock3,'Hàng chờ khám']],
  DOCTOR:[['/doctor',LayoutDashboard,'Khám bệnh'],['/doctor/queue',Clock3,'Bệnh nhân đang chờ'],['/doctor/schedule',CalendarDays,'Lịch làm việc']],
  ADMIN:[['/admin',BriefcaseMedical,'Quản trị hệ thống'],['/doctor/schedule',CalendarDays,'Lịch làm việc bác sĩ']],
};

export default function Layout({children}){
  const {user,logout}=useAuth(); const navigate=useNavigate(); const items=menus[user?.role]||[];
  return <div className="min-h-screen">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-[#dcecff] bg-white md:flex md:flex-col">
      <div className="px-6 py-6 border-b border-[#eef5fb]"><div className="flex items-center gap-3"><div className="h-11 w-11 rounded-2xl bg-[#2f80ed] text-white grid place-items-center shadow-lg"><Stethoscope size={22}/></div><div><div className="font-black text-[#17395f] text-lg">MedSchedule</div><div className="text-xs text-[#7a96b0]">Quản lý lịch khám</div></div></div></div>
      <nav className="p-4 space-y-1">{items.map(([to,Icon,label])=><NavLink key={to} to={to} end className={({isActive})=>`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition ${isActive?'bg-[#eaf4ff] text-[#2f80ed]':'text-[#58718e] hover:bg-[#f6faff]'}`}><Icon size={18}/>{label}</NavLink>)}</nav>
      <div className="mt-auto p-4"><div className="rounded-2xl bg-[#f4f9ff] p-4"><div className="text-sm font-black text-[#1c426b]">{user?.full_name}</div><div className="text-xs text-[#7691aa] mt-1">{roleLabel(user?.role)}</div>{user?.phone&&<div className="text-xs text-[#7691aa] mt-1">{user.phone}</div>}<button onClick={logout} className="btn btn-outline w-full mt-3"><LogOut size={16}/>Đăng xuất</button></div></div>
    </aside>
    <main className="md:ml-72 min-h-screen">
      <header className="sticky top-0 z-20 glass border-b border-[#dcecff] px-5 py-4"><div className="max-w-7xl mx-auto flex items-center justify-between"><div><div className="text-[11px] uppercase tracking-[.18em] text-[#79a0c7]">Workspace</div><div className="font-black text-[#183c63]">{roleWorkspace(user?.role)}</div></div><button onClick={()=>navigate('/')} className="btn btn-soft text-sm">Trang chủ</button></div></header>
      <div className="max-w-7xl mx-auto p-5 md:p-7">{children}</div>
    </main>
  </div>
}
function roleLabel(r){return {PATIENT:'Bệnh nhân',RECEPTIONIST:'Nhân viên tiếp nhận',DOCTOR:'Bác sĩ',ADMIN:'Quản trị viên'}[r]||'Người dùng'}
function roleWorkspace(r){return {PATIENT:'Khu vực bệnh nhân',RECEPTIONIST:'Quầy tiếp nhận',DOCTOR:'Phòng khám',ADMIN:'Quản trị hệ thống'}[r]||'MedSchedule'}
