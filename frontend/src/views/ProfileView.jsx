import { useCallback } from 'react';
import { User, BookOpen, LogOut, Target } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { useAuthStore } from '../store/authStore';
import { useAttendanceStore } from '../store/attendanceStore';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';

export default function ProfileView() {
  const fetchProfile = useCallback(() => api.get('/api/user/profile').then((r) => r.data), []);
  const { data: profile, isLoading } = useAsync(fetchProfile);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const targetPercentage = useAttendanceStore((s) => s.targetPercentage);
  const setTarget = useAttendanceStore((s) => s.setTargetPercentage);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="section-enter space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-ink tracking-tight">Profile</h1>
        <p className="text-sm text-ink-muted mt-1">Account info & settings</p>
      </div>

      {isLoading ? (
        <LoadingSpinner text="Loading profile…" />
      ) : profile ? (
        <>
          {/* User card */}
          <div className="card">
            <div className="flex items-center gap-4 mb-5">
              <div className="w-12 h-12 rounded-2xl bg-accent-light flex items-center justify-center">
                <User className="w-6 h-6 text-accent-text" />
              </div>
              <div>
                <p className="text-base font-semibold text-ink">{profile.username}</p>
                <p className="text-xs text-ink-faint">{profile.program}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <InfoRow icon={BookOpen} label="SRN" value={profile.srn} />
              <InfoRow icon={BookOpen} label="PESU ID" value={profile.pesu_id} />
              <InfoRow icon={BookOpen} label="Branch" value={profile.department} />
              <InfoRow icon={BookOpen} label="Semester" value={profile.semester} />
              <InfoRow icon={BookOpen} label="Section" value={profile.section} />
              <InfoRow icon={BookOpen} label="Email" value={profile.email} />
            </div>
          </div>

          {/* Settings */}
          <div className="card space-y-4">
            <p className="text-xs font-medium text-ink-faint uppercase tracking-wider">Settings</p>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-ink-muted" />
                <span className="text-sm text-ink">Target attendance</span>
              </div>
              <div className="flex items-center gap-1.5">
                {[75, 80, 85, 90].map((val) => (
                  <button
                    key={val}
                    onClick={() => setTarget(val)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                      targetPercentage === val
                        ? 'bg-accent text-white'
                        : 'bg-surface-1 text-ink-muted hover:bg-surface-2'
                    }`}
                  >
                    {val}%
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="card card-hover w-full flex items-center gap-3 text-left text-bad hover:border-bad/30 hover:bg-bad-light transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-medium">Sign out</span>
          </button>
        </>
      ) : null}
    </div>
  );
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="w-3.5 h-3.5 text-ink-faint mt-0.5 shrink-0" />
      <div>
        <p className="text-xs text-ink-faint">{label}</p>
        <p className="text-sm text-ink font-medium">{value || '—'}</p>
      </div>
    </div>
  );
}

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}
