import { useState, useCallback } from 'react';
import { Clock, ChevronRight } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { timetableService } from '../services/timetableService';
import LoadingSpinner from '../components/LoadingSpinner';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Muted palette — each course gets a consistent accent
const COURSE_COLORS = [
  'bg-accent-light text-accent-text border-accent/15',
  'bg-ok-light text-ok border-ok/15',
  'bg-warn-light text-warn border-warn/15',
  'bg-bad-light text-bad border-bad/15',
  'bg-surface-2 text-ink-muted border-line',
  'bg-purple-50 text-purple-700 border-purple-200',
];

export default function TimetableView() {
  const [view, setView] = useState('today');

  const fetchToday = useCallback(() => timetableService.getToday(), []);
  const fetchWeek = useCallback(() => timetableService.getWeek(), []);

  const todayResult = useAsync(fetchToday, view === 'today');
  const weekResult = useAsync(fetchWeek, view === 'week');

  const isLoading = view === 'today' ? todayResult.isLoading : weekResult.isLoading;
  const error = view === 'today' ? todayResult.error : weekResult.error;

  // Build a color map from unique course codes
  const getColorMap = (classes) => {
    const map = {};
    let idx = 0;
    classes.forEach((c) => {
      if (!map[c.course_code]) {
        map[c.course_code] = COURSE_COLORS[idx % COURSE_COLORS.length];
        idx++;
      }
    });
    return map;
  };

  return (
    <div className="section-enter space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink tracking-tight">Timetable</h1>
          <p className="text-sm text-ink-muted mt-1">
            {view === 'today' ? 'Today's schedule' : 'Weekly overview'}
          </p>
        </div>
        <div className="flex bg-surface-1 rounded-xl p-0.5">
          {['today', 'week'].map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                view === v ? 'bg-white text-ink shadow-card' : 'text-ink-muted'
              }`}
            >
              {v === 'today' ? 'Today' : 'Week'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingSpinner text="Loading timetable…" />
      ) : error ? (
        <div className="card border-bad/30 bg-bad-light text-bad text-sm p-4">{error}</div>
      ) : view === 'today' ? (
        <TodayView data={todayResult.data} getColorMap={getColorMap} />
      ) : (
        <WeekView data={weekResult.data} getColorMap={getColorMap} />
      )}
    </div>
  );
}

function TodayView({ data, getColorMap }) {
  if (!data || !data.classes || data.classes.length === 0) {
    return (
      <div className="card text-center py-12">
        <Clock className="w-8 h-8 text-ink-faint mx-auto mb-3" />
        <p className="text-sm text-ink-muted">No classes scheduled for {data?.day || 'today'}</p>
      </div>
    );
  }

  const colorMap = getColorMap(data.classes);

  return (
    <div className="space-y-2">
      <p className="text-xs text-ink-faint font-medium uppercase tracking-wider px-1">
        {data.day} · {data.total_classes} classes
      </p>
      {data.classes.map((cls, i) => (
        <div
          key={i}
          className={`card flex items-center gap-4 animate-slide-up`}
          style={{ animationDelay: `${i * 0.04}s`, animationFillMode: 'both' }}
        >
          {/* Time */}
          <div className="shrink-0 w-20 text-right">
            <p className="text-xs font-mono text-ink-muted tabular-nums">
              {cls.time || '—'}
            </p>
          </div>
          {/* Divider */}
          <div className={`w-1 h-10 rounded-full ${colorMap[cls.course_code]?.split(' ')[0] || 'bg-surface-2'}`} />
          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-ink truncate">{cls.course_name}</p>
            <p className="text-xs text-ink-faint mt-0.5">
              {cls.course_code}{cls.instructor ? ` · ${cls.instructor}` : ''}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function WeekView({ data, getColorMap }) {
  if (!data || !data.week || Object.keys(data.week).length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-sm text-ink-muted">No timetable data available</p>
      </div>
    );
  }

  // Get all unique courses across the week for a consistent color map
  const allClasses = Object.values(data.week).flat();
  const colorMap = getColorMap(allClasses);

  return (
    <div className="space-y-4">
      {DAYS.map((day) => {
        const classes = data.week[day];
        if (!classes || classes.length === 0) return null;
        return (
          <div key={day}>
            <p className="text-xs font-medium text-ink-faint uppercase tracking-wider px-1 mb-2">
              {day} · {classes.length} classes
            </p>
            <div className="space-y-1.5">
              {classes.map((cls, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border ${colorMap[cls.course_code] || 'bg-surface-1 text-ink-muted border-line'}`}
                >
                  <span className="text-xs font-mono shrink-0 w-24 tabular-nums">
                    {cls.time || '—'}
                  </span>
                  <span className="text-xs font-medium truncate flex-1">
                    {cls.course_name}
                  </span>
                  <span className="text-xs opacity-70 hidden sm:block">
                    {cls.instructor}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
