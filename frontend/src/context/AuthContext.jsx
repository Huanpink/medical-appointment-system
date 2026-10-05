import {createContext,useContext,useEffect,useState} from 'react';
import {authApi} from '../services/api';
const C=createContext(null);export const useAuth=()=>useContext(C);
export function AuthProvider({children}){const [user,setUser]=useState(()=>{try{return JSON.parse(localStorage.getItem('med_user'))}catch{return null}});const [loading,setLoading]=useState(!!localStorage.getItem('med_token'));
 useEffect(()=>{if(localStorage.getItem('med_token'))authApi.me().then(r=>{setUser(r.data);localStorage.setItem('med_user',JSON.stringify(r.data))}).catch(()=>{}).finally(()=>setLoading(false));},[]);
 const login=async(d)=>{const r=await authApi.login(d);localStorage.setItem('med_token',r.data.access_token);localStorage.setItem('med_user',JSON.stringify(r.data.user));setUser(r.data.user)};
 const register=async(d)=>{const r=await authApi.register(d);localStorage.setItem('med_token',r.data.access_token);localStorage.setItem('med_user',JSON.stringify(r.data.user));setUser(r.data.user)};
 const logout=()=>{localStorage.removeItem('med_token');localStorage.removeItem('med_user');setUser(null);window.location.hash='#/login'};return <C.Provider value={{user,loading,login,register,logout}}>{children}</C.Provider>}
