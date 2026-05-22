import { useCallback, useState } from 'react';
import { RefreshCw, Target } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { attendanceService } from '../services/attendanceService';
import { useAttendanceStore } from '../store/attendanceStore';
import LoadingSpinner from '../components/LoadingSpinner';

export default function AttendanceView({ onCourseSelect }) {
  const fetchCourses = useCallback(() => attendanceService.getCourses(), []);
  const { data, isLoading, error, execute } = useAsync(fetchCourses);
  const targetPercentage = useAttendanceStore((s) => s.targetPercentage);
  const setTarget = useAttendanceStore((s) => s.setTargetPercentage);

  const [syncing, setSyncing] = useState(false);
  const [customTarget, setCustomTarget] = useState('');

  const courses = data?.courses || [];

  const handleSync = async () => {
    setSyncing(true);
    try {
      await attendanceService.sync();
      await execute();
    } catch (_) {
      // ignore
    } finally {
      setSyncing(false);
    }
  };

  const handleCustomTarget = () => {
    const val = parseInt(customTarget, 10);
    if (val >= 1 && val <= 100) {
      setTarget(val);
      setCustomTarget('');
    }
  };

  return (
    <div className="section-enter space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink tracking-tight">Attendance</h1>
          <p className="text-sm text-ink-muted mt-1">Course-wise breakdown</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-ghost text-xs shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing…' : 'Sync'}
        </button>
      </div>

      {/* Target setting */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-4 h-4 text-ink-muted" />
          <span className="text-xs font-medium text-ink-muted uppercase tracking-wider">
            Target attendance
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {[85, 80, 75].map((val) => (
            <button
              key={val}
              onClick={() => setTarget(val)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                targetPercentage === val
                  ? 'bg-accent text-white'
                  : 'bg-surface-1 text-ink-muted hover:bg-surface-2'
              }`}
            >
              {val}%
            </button>
          ))}
          <div className="flex items-center gap-1.5">
            <input
              type="number"
              min="1"
              max="100"
              value={customTarget}
              onChange={(e) => setCustomTarget(e.target.value)}
              placeholder="Custom"
              className="input-base w-20 text-xs py-1.5"
              onKeyDown={(e) => e.key === 'Enter' && handleCustomTarget()}
            />
            {customTarget && (
              <button onClick={handleCustomTarget} className="btn-ghost text-xs py-1.5 px-2">
                Set
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Course list */}
      {isLoading ? (
        <LoadingSpinner text="Loading courses…" />
      ) : error ? (
        <div className="card border-bad/30 bg-bad-light text-bad text-sm p-4">
          {error}
        </div>
      ) : (
        <div className="space-y-2">
          {courses.map((course, i) => (
            <CourseCard
              key={course.course_code}
              course={course}
              target={targetPercentage}
              index={i}
              onClick={() => onCourseSelect(course)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CourseCard({ course, target, index, onClick }) {
  const { course_code, course_name, attendance, requirement } = course;
  const pct = attendance.percentage;
  const isBelow = pct < target;
  const shortage = requirement?.shortage || 0;

  // Bunk allowance calc (client-side)
  const canBunk =
    pct >= target
      ? Math.floor((attendance.attended * 100) / target - attendance.total)
      : 0;

  const barColor = pct >= target ? 'bg-ok' : pct >= target - 10 ? 'bg-warn' : 'bg-bad';

  return (
    <button
      onClick={onClick}
      className="card card-hover w-full text-left animate-slide-up"
      style={{ animationDelay: `${index * 0.04}s`, animationFillMode: 'both' }}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink truncate">{course_name}</p>
          <p className="text-xs text-ink-faint font-mono mt-0.5">{course_code}</p>
        </div>
        <div className="text-right shrink-0">
          <p className={`text-lg font-bold tabular-nums ${isBelow ? 'text-bad' : 'text-ok'}`}>
            {pct}%
          </p>
        </div>
      </div>

      {/* Bar */}
      <div className="att-bar mb-3">
        <div
          className={`att-bar-fill ${barColor}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>

      {/* Bottom row */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-ink-muted tabular-nums">
          {attendance.attended}/{attendance.total} classes
        </span>
        {isBelow ? (
          <span className="badge-bad">Need {shortage} more</span>
        ) : canBunk > 0 ? (
          <span className="badge-ok">Can skip {canBunk}</span>
        ) : (
          <span className="badge-warn">No skips left</span>
        )}
      </div>
    </button>
  );
}
