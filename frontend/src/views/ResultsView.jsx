import { useState, useCallback } from 'react';
import { Award, ChevronDown } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { resultsService } from '../services/resultsService';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ResultsView() {
  const fetchResults = useCallback(() => resultsService.getAll(), []);
  const { data, isLoading, error } = useAsync(fetchResults);

  const semesters = data?.semesters || [];
  const [activeSem, setActiveSem] = useState(null);

  // Default to first semester once loaded
  if (semesters.length > 0 && activeSem === null) {
    // Use timeout-free approach — just render with first
  }
  const currentSem = activeSem ?? semesters[0]?.semester;
  const semData = semesters.find((s) => s.semester === currentSem);

  return (
    <div className="section-enter space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-ink tracking-tight">Results</h1>
        <p className="text-sm text-ink-muted mt-1">Exam scores & assessments</p>
      </div>

      {isLoading ? (
        <LoadingSpinner text="Loading results…" />
      ) : error ? (
        <div className="card border-bad/30 bg-bad-light text-bad text-sm p-4">{error}</div>
      ) : semesters.length === 0 ? (
        <div className="card text-center py-12">
          <Award className="w-8 h-8 text-ink-faint mx-auto mb-3" />
          <p className="text-sm text-ink-muted">No results available yet</p>
        </div>
      ) : (
        <>
          {/* Semester tabs */}
          <div className="flex bg-surface-1 rounded-xl p-0.5 w-fit">
            {semesters.map(({ semester }) => (
              <button
                key={semester}
                onClick={() => setActiveSem(semester)}
                className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  currentSem === semester
                    ? 'bg-white text-ink shadow-card'
                    : 'text-ink-muted hover:text-ink'
                }`}
              >
                {semester}
              </button>
            ))}
          </div>

          {/* Courses */}
          {semData && (
            <div className="space-y-2">
              <p className="text-xs text-ink-faint px-1">
                {semData.course_count} courses · {semData.type}
              </p>
              {semData.courses.map((course, i) => (
                <ResultCard key={course.course_code} course={course} index={i} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ResultCard({ course, index }) {
  const [open, setOpen] = useState(false);
  const { course_code, course_name, assessments, marks } = course;

  const assessmentEntries = Object.entries(assessments || {});

  return (
    <div
      className="card animate-slide-up"
      style={{ animationDelay: `${index * 0.04}s`, animationFillMode: 'both' }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 text-left"
      >
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink truncate">{course_name}</p>
          <p className="text-xs text-ink-faint font-mono mt-0.5">{course_code}</p>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-ink-faint shrink-0 transition-transform duration-200 ${
            open ? 'rotate-180' : ''
          }`}
        />
      </button>

      {open && assessmentEntries.length > 0 && (
        <div className="mt-4 border-t border-line pt-3 space-y-2.5 animate-fade-in">
          {assessmentEntries.map(([name, rawValue]) => {
            const markData = marks?.[name];
            const obtained = markData?.obtained;
            const total = markData?.total;
            const hasScore = obtained !== undefined && total !== undefined;
            const pct = hasScore ? (parseFloat(obtained) / parseFloat(total)) * 100 : null;

            return (
              <div key={name}>
                <div className="flex justify-between items-center text-sm mb-1">
                  <span className="text-ink-muted">{name}</span>
                  <span className="font-medium text-ink tabular-nums">
                    {hasScore ? `${obtained} / ${total}` : rawValue}
                  </span>
                </div>
                {pct !== null && (
                  <div className="att-bar">
                    <div
                      className={`att-bar-fill ${
                        pct >= 70 ? 'bg-ok' : pct >= 50 ? 'bg-warn' : 'bg-bad'
                      }`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
