import { useState } from 'react';
import { ArrowLeft, Calculator, CheckCircle2, XCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useAttendanceStore } from '../store/attendanceStore';
import { useAttendanceCalculator } from '../hooks/useAttendanceCalculator';

export default function CourseDetailView({ course, onBack }) {
  const { course_code, course_name, attendance, requirement } = course;
  const targetPercentage = useAttendanceStore((s) => s.targetPercentage);

  const { calculateCombined, required } =
    useAttendanceCalculator(attendance.attended, attendance.total, targetPercentage);

  const [attendInput, setAttendInput] = useState(0);
  const [skipInput, setSkipInput] = useState(0);

  const pct = attendance.percentage;
  const isBelow = pct < targetPercentage;

  const combinedResult = calculateCombined(attendInput, skipInput);
  const hasInput = attendInput > 0 || skipInput > 0;

  // Pie chart data
  const pieData = [
    { name: 'Present', value: attendance.attended },
    { name: 'Absent', value: attendance.total - attendance.attended },
  ];
  const PIE_COLORS = ['#2D8C4E', '#E3E3E0'];

  return (
    <div className="section-enter space-y-5">
      {/* Back + header */}
      <div>
        <button onClick={onBack} className="btn-ghost text-xs mb-3 -ml-2">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to courses
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-ink tracking-tight">{course_name}</h1>
            <p className="text-xs text-ink-faint font-mono mt-1">{course_code}</p>
          </div>
          <div className="text-right">
            <p className={`text-3xl font-bold tabular-nums ${isBelow ? 'text-bad' : 'text-ok'}`}>
              {pct}%
            </p>
            <p className="text-xs text-ink-faint mt-0.5">Target: {targetPercentage}%</p>
          </div>
        </div>
      </div>

      {/* Stats + chart row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Chart */}
        <div className="card flex flex-col items-center justify-center py-6">
          <div className="w-36 h-36 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={60}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-ink tabular-nums">
                {attendance.attended}/{attendance.total}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-ok" /> Present
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-surface-3" /> Absent
            </span>
          </div>
        </div>

        {/* Status card */}
        <div className="card space-y-3">
          <p className="text-xs font-medium text-ink-faint uppercase tracking-wider">Status</p>
          <div className="space-y-2.5">
            <StatusRow
              label="Attended"
              value={`${attendance.attended} classes`}
            />
            <StatusRow label="Total" value={`${attendance.total} classes`} />
            <StatusRow label="Absent" value={`${attendance.total - attendance.attended} classes`} />
            <div className="border-t border-line pt-2.5">
              <StatusRow
                label={`Need for ${targetPercentage}%`}
                value={
                  required.isOnTrack
                    ? '✓ On track'
                    : `${required.classesNeededToAttend} more`
                }
                highlight={!required.isOnTrack}
              />
              <StatusRow
                label="Can safely skip"
                value={
                  required.isOnTrack
                    ? `${required.classesCanBunk} classes`
                    : '0 classes'
                }
              />
            </div>
          </div>
        </div>
      </div>

      {/* ——— Combined Calculator ——— */}
      <div className="card p-0 overflow-hidden">
        <div className="px-5 pt-5 pb-3 flex items-center gap-2">
          <Calculator className="w-4 h-4 text-ink-muted" />
          <h2 className="text-sm font-semibold text-ink">What-If Calculator</h2>
        </div>

        <div className="px-5 pb-4">
          <p className="text-xs text-ink-muted mb-4">
            Enter the number of upcoming classes you plan to attend and skip to see your projected attendance.
          </p>

          <div className="grid grid-cols-2 gap-3">
            {/* Attend input */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-ok">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wider">
                  I'll attend
                </span>
              </div>
              <input
                type="number"
                min="0"
                max="200"
                value={attendInput}
                onChange={(e) => setAttendInput(Math.max(0, parseInt(e.target.value) || 0))}
                className="input-base text-sm"
                placeholder="0 classes"
              />
            </div>

            {/* Skip input */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-bad">
                <XCircle className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wider">
                  I'll skip
                </span>
              </div>
              <input
                type="number"
                min="0"
                max="200"
                value={skipInput}
                onChange={(e) => setSkipInput(Math.max(0, parseInt(e.target.value) || 0))}
                className="input-base text-sm"
                placeholder="0 classes"
              />
            </div>
          </div>

          {/* Combined Result */}
          {hasInput && (
            <div className="mt-4 p-4 rounded-xl bg-surface-1 animate-fade-in space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-ink-muted">Projected attendance</span>
                <span className={`text-xl font-bold tabular-nums ${combinedResult.meetsTarget ? 'text-ok' : 'text-bad'}`}>
                  {combinedResult.newPercentage.toFixed(1)}%
                </span>
              </div>

              <div className="att-bar">
                <div
                  className={`att-bar-fill ${combinedResult.meetsTarget ? 'bg-ok' : 'bg-bad'}`}
                  style={{ width: `${Math.min(100, combinedResult.newPercentage)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-ink-muted tabular-nums">
                  {combinedResult.newAttended}/{combinedResult.newTotal} classes
                </span>
                <span className={`tabular-nums font-medium ${combinedResult.change >= 0 ? 'text-ok' : 'text-bad'}`}>
                  {combinedResult.change >= 0 ? '+' : ''}{combinedResult.change.toFixed(1)}% from current
                </span>
              </div>

              {combinedResult.meetsTarget ? (
                <p className="text-xs text-ok flex items-center gap-1 font-medium">
                  <CheckCircle2 className="w-3 h-3" /> Meets {targetPercentage}% target
                </p>
              ) : (
                <p className="text-xs text-bad flex items-center gap-1 font-medium">
                  <XCircle className="w-3 h-3" /> Below {targetPercentage}% target
                </p>
              )}
            </div>
          )}
        </div>

        {/* Summary row */}
        <div className="border-t border-line px-5 py-4 bg-surface-1/50">
          <p className="text-xs font-medium text-ink-faint uppercase tracking-wider mb-2.5">
            What you need
          </p>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 text-sm">
            <span className="text-ink">
              Must attend:{' '}
              <strong className={required.isOnTrack ? 'text-ok' : 'text-accent'}>
                {required.classesNeededToAttend} classes
              </strong>
            </span>
            <span className="text-ink">
              Can safely skip:{' '}
              <strong className={required.classesCanBunk > 0 ? 'text-ok' : 'text-bad'}>
                {required.classesCanBunk} classes
              </strong>
            </span>
            <span className="ml-auto">
              {required.isOnTrack ? (
                <span className="badge-ok">On Track</span>
              ) : (
                <span className="badge-bad">Below Target</span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Shortage info */}
      {requirement?.shortage > 0 && (
        <div className="flex items-start gap-3 px-4 py-3.5 rounded-2xl bg-bad-light border border-bad/15 text-sm text-bad">
          <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <p>
            You are <strong>{requirement.shortage} classes</strong> short of the{' '}
            {requirement.minimum_percentage}% requirement.
            {requirement.required_classes > 0 && (
              <> You need at least {requirement.required_classes} attended out of {attendance.total}.</>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

function StatusRow({ label, value, highlight = false }) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-ink-muted">{label}</span>
      <span className={`font-medium tabular-nums ${highlight ? 'text-bad' : 'text-ink'}`}>
        {value}
      </span>
    </div>
  );
}
