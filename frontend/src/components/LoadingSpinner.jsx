import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ text = 'Loading…', className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-16 ${className}`}>
      <Loader2 className="w-6 h-6 text-ink-faint animate-spin" />
      <p className="text-sm text-ink-faint">{text}</p>
    </div>
  );
}
