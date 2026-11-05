"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { CircleAlert, CircleCheck, Info } from "lucide-react";

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

const STYLES = {
  success: { icon: CircleCheck, color: "var(--success)" },
  error: { icon: CircleAlert, color: "var(--danger)" },
  info: { icon: Info, color: "var(--primary)" },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(0);

  const show = useCallback((message, type = "success") => {
    const id = nextId.current++;
    setToasts((current) => [...current, { id, message, type }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), 4000);
  }, []);

  const value = useMemo(() => show, [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="fixed inset-x-4 top-20 z-50 flex flex-col items-end gap-2 md:left-auto md:right-6 md:w-96"
        role="status"
        aria-live="polite"
      >
        {toasts.map(({ id, message, type }) => {
          const { icon: Icon, color } = STYLES[type];
          return (
            <div key={id} className="glass-panel animate-slide-up flex w-full items-start gap-3 rounded-2xl p-4 shadow-[0_15px_40px_rgba(0,0,0,0.08)]">
              <Icon className="mt-0.5 h-5 w-5 shrink-0" style={{ color }} aria-hidden />
              <p className="text-sm font-bold">{message}</p>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
