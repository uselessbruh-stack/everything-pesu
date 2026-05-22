import { useState } from 'react';
import { ArrowLeft, TrendingUp, TrendingDown, Calculator, CheckCircle2, XCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useAttendanceStore } from '../store/attendanceStore';
import { useAttendanceCalculator } from '../hooks/useAttendanceCalculator';

export default function CourseDetailView({ course, onBack }) {
  const { course_code, course_name, attendance, requirement } = course;
  const targetPercentage = useAttendanceStore((s) => s.targetPercentage);

  const { calculateAttendMore, calculateBunkClasses, required } =
    useAttendanceCalculator(attendance.attended, attendance.total, targetPercentage);

  const [attendInput, setAttendInput] = useState(0);
  const [bunkInput, setBunkInput] = useState(0);

  const pct = attendance.percentage;
  const isBelow = pct < targetPercentage;

  const attendResult = calculateAttendMore(attendInput);
  const bunkResult = calculateBunkClasses(bunkInput);

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

      {/* ——— Calculator ——— */}
      <div className="card p-0 overflow-hidden">
        <div className="px-5 pt-5 pb-3 flex items-center gap-2">
          <Calculator className="w-4 h-4 text-ink-muted" />
          <h2 className="text-sm font-semibold text-ink">Attendance Calculator</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-line">
          {/* Attend scenario */}
          <div className="p-5 space-y-3">
            <div className="flex items-center gap-2 text-ok">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wider">
                If I attend more
              </span>
            </div>
            <input
              type="number"
              min="0"
              max="200"
              value={attendInput}
              onChange={(e) => setAttendInput(Math.max(0, parseInt(e.target.value) || 0))}
              className="input-base text-sm"
              placeholder="Number of classes"
            />
            {attendInput > 0 && (
              <div className="animate-fade-in space-y-1.5">
                <p className="text-sm font-semibold text-ink tabular-nums">
                  {attendResult.newAttended}/{attendResult.newTotal} ={' '}
                  {attendResult.newPercentage.toFixed(1)}%
                </p>
                {attendResult.meetsTarget ? (
                  <p className="text-xs text-ok flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Meets target
                  </p>
                ) : (
                  <p className="text-xs text-warn flex items-center gap-1">
                    <XCircle className="w-3 h-3" /> Still below {targetPercentage}%
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Bunk scenario */}
          <div className="p-5 space-y-3">
            <div className="flex items-center gap-2 text-bad">
              <TrendingDown className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wider">
                If I skip classes
              </span>
            </div>
            <input
              type="number"
              min="0"
              max="200"
              value={bunkInput}
              onChange={(e) => setBunkInput(Math.max(0, parseInt(e.target.value) || 0))}
              className="input-base text-sm"
              placeholder="Number of classes"
            />
            {bunkInput > 0 && (
              <div className="animate-fade-in space-y-1.5">
                <p className="text-sm font-semibold text-ink tabular-nums">
                  {bunkResult.newAttended}/{bunkResult.newTotal} ={' '}
                  {bunkResult.newPercentage.toFixed(1)}%
                </p>
                {bunkResult.meetsTarget ? (
                  <p className="text-xs text-ok flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Still above target
                  </p>
                ) : (
                  <p className="text-xs text-bad flex items-center gap-1 font-medium">
                    <XCircle className="w-3 h-3" /> Below target!
                  </p>
                )}
              </div>
            )}
          </div>
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
