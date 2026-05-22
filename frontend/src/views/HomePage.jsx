import { useCallback, useEffect } from 'react';
import { BarChart3, Calendar, FileText, User, TrendingDown, AlertCircle, ArrowRight } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { attendanceService } from '../services/attendanceService';
import { useAttendanceStore } from '../store/attendanceStore';

const SECTION_CARDS = [
  {
    id: 'attendance',
    label: 'Attendance',
    desc: 'Course-wise breakdown & calculator',
    icon: BarChart3,
    color: 'bg-accent-light text-accent-text',
  },
  {
    id: 'timetable',
    label: 'Timetable',
    desc: 'Today\'s schedule & weekly view',
    icon: Calendar,
    color: 'bg-ok-light text-ok',
  },
  {
    id: 'results',
    label: 'Results',
    desc: 'Exam scores & assessments',
    icon: FileText,
    color: 'bg-warn-light text-warn',
  },
  {
    id: 'profile',
    label: 'Profile',
    desc: 'Account info & settings',
    icon: User,
    color: 'bg-surface-2 text-ink-muted',
  },
];

export default function HomePage({ onNavigate }) {
  const fetchSummary = useCallback(() => attendanceService.getSummary(), []);
  const { data: summary, isLoading, error } = useAsync(fetchSummary);
  const setSummary = useAttendanceStore((s) => s.setSummary);

  useEffect(() => {
    if (summary) setSummary(summary);
  }, [summary, setSummary]);

  const pct = summary?.overall_percentage ?? 0;
  const pctColor =
    pct >= 85 ? 'text-ok' : pct >= 75 ? 'text-warn' : 'text-bad';

  return (
    <div className="section-enter space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-2xl font-semibold text-ink tracking-tight">Overview</h1>
        <p className="text-sm text-ink-muted mt-1">Your attendance at a glance</p>
      </div>

      {/* ——— Summary card ——— */}
      {isLoading ? (
        <SummarySkeleton />
      ) : error ? (
        <div className="card border-bad/30 bg-bad-light text-bad text-sm p-4">
          <AlertCircle className="w-4 h-4 inline mr-1.5" />
          Failed to load summary. {error}
        </div>
      ) : summary ? (
        <div className="card p-0 overflow-hidden">
          {/* Top row */}
          <div className="px-5 pt-5 pb-4 flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-ink-faint uppercase tracking-wider mb-1">
                Overall attendance
              </p>
              <p className={`text-4xl font-bold tabular-nums tracking-tight ${pctColor}`}>
                {pct.toFixed(1)}
                <span className="text-lg font-medium">%</span>
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-ink-faint mb-1">Classes</p>
              <p className="text-lg font-semibold text-ink tabular-nums">
                {summary.total_attended}
                <span className="text-ink-faint font-normal">/{summary.total_classes}</span>
              </p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="px-5 pb-4">
            <div className="att-bar">
              <div
                className={`att-bar-fill ${
                  pct >= 85 ? 'bg-ok' : pct >= 75 ? 'bg-warn' : 'bg-bad'
                }`}
                style={{ width: `${Math.min(100, pct)}%` }}
              />
            </div>
          </div>

          {/* Stats row */}
          <div className="border-t border-line grid grid-cols-3 divide-x divide-line">
            <StatCell
              label="Courses"
              value={summary.courses_count}
            />
            <StatCell
              label="Below 85%"
              value={summary.courses_below_requirement}
              warn={summary.courses_below_requirement > 0}
            />
            <StatCell
              label="Shortage"
              value={`${summary.total_shortage} cls`}
              warn={summary.total_shortage > 0}
            />
          </div>
        </div>
      ) : null}

      {/* ——— Quick warning ——— */}
      {summary && summary.courses_below_requirement > 0 && (
        <div className="flex items-start gap-3 px-4 py-3.5 rounded-2xl bg-warn-light border border-warn/15 animate-fade-in">
          <TrendingDown className="w-4 h-4 text-warn mt-0.5 shrink-0" />
          <p className="text-sm text-warn">
            <span className="font-medium">{summary.courses_below_requirement} course{summary.courses_below_requirement > 1 ? 's' : ''}</span> below the 85% requirement.
            You need to attend <span className="font-medium">{summary.total_shortage}</span> more classes total.
          </p>
        </div>
      )}

      {/* ——— Navigation cards ——— */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {SECTION_CARDS.map(({ id, label, desc, icon: Icon, color }, i) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className="card card-hover text-left group flex items-center gap-4 animate-slide-up"
            style={{ animationDelay: `${i * 0.06}s`, animationFillMode: 'both' }}
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-ink">{label}</p>
              <p className="text-xs text-ink-faint mt-0.5">{desc}</p>
            </div>
            <ArrowRight className="w-4 h-4 text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        ))}
      </div>
    </div>
  );
}

function StatCell({ label, value, warn = false }) {
  return (
    <div className="py-3 px-4 text-center">
      <p className="text-xs text-ink-faint mb-0.5">{label}</p>
      <p className={`text-base font-semibold tabular-nums ${warn ? 'text-bad' : 'text-ink'}`}>
        {value}
      </p>
    </div>
  );
}

function SummarySkeleton() {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex justify-between">
        <div className="space-y-2">
          <div className="skeleton h-3 w-28 rounded" />
          <div className="skeleton h-10 w-32 rounded-lg" />
        </div>
        <div className="space-y-2 text-right">
          <div className="skeleton h-3 w-16 rounded ml-auto" />
          <div className="skeleton h-6 w-20 rounded ml-auto" />
        </div>
      </div>
      <div className="skeleton h-1.5 w-full rounded-full" />
      <div className="grid grid-cols-3 gap-4 pt-3 border-t border-line">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex flex-col items-center gap-1.5">
            <div className="skeleton h-3 w-14 rounded" />
            <div className="skeleton h-5 w-8 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
