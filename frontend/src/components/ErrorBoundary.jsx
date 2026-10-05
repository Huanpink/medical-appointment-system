import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: typeof error?.message === 'string' ? error.message : 'Đã xảy ra lỗi giao diện.' };
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="min-h-screen bg-[#eef7ff] grid place-items-center p-6">
        <div className="max-w-lg rounded-2xl bg-white p-8 shadow-xl">
          <h1 className="text-xl font-bold text-[#193b63]">Không thể hiển thị trang</h1>
          <p className="mt-3 text-sm text-[#64809c]">Vui lòng tải lại trang. Nếu lỗi vẫn còn, kiểm tra Console để biết chi tiết.</p>
          <p className="mt-3 break-words text-xs text-[#8aa0b5]">{this.state.message}</p>
          <button className="btn btn-primary mt-6" onClick={() => window.location.reload()}>Tải lại</button>
        </div>
      </div>
    );
  }
}
