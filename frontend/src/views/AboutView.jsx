import { useState, useEffect } from 'react';
import {
  Star,
  GitFork,
  AlertCircle,
  Send,
  MessageSquare,
  Sparkles,
  Sun,
  Moon,
  CheckCircle2,
  Code
} from 'lucide-react';
import { feedbackService } from '../services/feedbackService';
import { useThemeStore } from '../store/themeStore';

const GITHUB_REPO = 'uselessbruh-stack/everything-pesu';
const HAS_RATED_KEY = 'everything_pesu_has_rated';

function GithubIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

export default function AboutView() {
  // Theme state
  const { theme, toggleTheme } = useThemeStore();

  // GitHub stats state
  const [gitStats, setGitStats] = useState({
    stars: 0,
    forks: 0,
    issues: 0,
    loading: true,
    error: false,
  });

  // Ratings state
  const [ratingStats, setRatingStats] = useState({
    average: 0.0,
    total: 0,
    loading: true,
  });
  const [userRating, setUserRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [hasRated, setHasRated] = useState(false);
  const [submittingRating, setSubmittingRating] = useState(false);
  const [ratingSuccess, setRatingSuccess] = useState(false);

  // Contact form state
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [submittingContact, setSubmittingContact] = useState(false);
  const [contactSuccess, setContactSuccess] = useState(false);
  const [contactError, setContactError] = useState('');

  // Fetch data on load
  useEffect(() => {
    // 1. Check if user already rated
    if (localStorage.getItem(HAS_RATED_KEY)) {
      setHasRated(true);
    }

    // 2. Fetch GitHub details
    fetch(`https://api.github.com/repos/${GITHUB_REPO}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch github stats');
        return res.json();
      })
      .then((data) => {
        setGitStats({
          stars: data.stargazers_count,
          forks: data.forks_count,
          issues: data.open_issues_count,
          loading: false,
          error: false,
        });
      })
      .catch((err) => {
        console.error(err);
        setGitStats((prev) => ({ ...prev, loading: false, error: true }));
      });

    // 3. Fetch Rating stats
    feedbackService.getRatings()
      .then((data) => {
        setRatingStats({
          average: data.average_rating,
          total: data.total_ratings,
          loading: false,
        });
      })
      .catch((err) => {
        console.error('Error fetching rating stats:', err);
        setRatingStats((prev) => ({ ...prev, loading: false }));
      });
  }, []);

  // Handle rating submission
  const handleRatingSubmit = async (e) => {
    e.preventDefault();
    if (userRating < 1 || userRating > 5) return;

    setSubmittingRating(true);
    try {
      const result = await feedbackService.submitRating(userRating, feedbackComment);
      if (result.ratings) {
        setRatingStats({
          average: result.ratings.average_rating,
          total: result.ratings.total_ratings,
          loading: false,
        });
      }
      localStorage.setItem(HAS_RATED_KEY, 'true');
      setHasRated(true);
      setRatingSuccess(true);
    } catch (err) {
      console.error('Error submitting rating:', err);
    } finally {
      setSubmittingRating(false);
    }
  };

  // Handle contact form submit
  const handleContactSubmit = async (e) => {
    e.preventDefault();
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      setContactError('Please fill in all the fields.');
      return;
    }

    setSubmittingContact(true);
    setContactError('');
    setContactSuccess(false);

    try {
      await feedbackService.sendContactMessage(
        contactForm.name,
        contactForm.email,
        contactForm.message
      );
      setContactSuccess(true);
      setContactForm({ name: '', email: '', message: '' });
    } catch (err) {
      console.error(err);
      setContactError(
        err.response?.data?.detail || 'Could not send contact message. Please try again.'
      );
    } finally {
      setSubmittingContact(false);
    }
  };

  return (
    <div className="section-enter space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink dark:text-dark-ink tracking-tight">About everything-pesu</h1>
          <p className="text-sm text-ink-muted dark:text-dark-muted mt-1">Application details, ratings, repository status, and support.</p>
        </div>

        {/* Dynamic Theme Switcher Card */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3 py-2 rounded-xl border border-line dark:border-dark-line bg-white dark:bg-dark-1 hover:bg-surface-1 dark:hover:bg-dark-2 text-ink-muted dark:text-dark-muted hover:text-ink dark:hover:text-dark-ink transition-colors cursor-pointer select-none"
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-4 h-4 text-warn" />
              <span className="text-xs font-medium">Light Mode</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-accent" />
              <span className="text-xs font-medium">Dark Mode</span>
            </>
          )}
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        
        {/* Left Side: GitHub Stats & Description */}
        <div className="space-y-5">
          {/* App Info Card */}
          <div className="card bg-white dark:bg-dark-1 border-line dark:border-dark-line">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-accent-light dark:bg-accent/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-accent-text" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-ink dark:text-dark-ink">Everything PESU</h3>
                <p className="text-xs text-ink-faint dark:text-dark-faint">Version 2.0.0 (PWA)</p>
              </div>
            </div>
            <p className="text-sm text-ink-muted dark:text-dark-muted leading-relaxed">
              Everything PESU is a modern, responsive companion app for PESU Academy. It scrapes live attendance, course details, timetable schedules, and grades securely directly from your student profile. No local JSON cache is used, and credentials are handled securely.
            </p>
          </div>

          {/* GitHub Repository Stats Card */}
          <div className="card bg-white dark:bg-dark-1 border-line dark:border-dark-line">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <GithubIcon className="w-5 h-5 text-ink dark:text-dark-ink" />
                <h3 className="text-sm font-semibold text-ink dark:text-dark-ink">GitHub Repository</h3>
              </div>
              <a
                href={`https://github.com/${GITHUB_REPO}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-accent hover:underline font-medium"
              >
                View Repository
              </a>
            </div>

            {gitStats.loading ? (
              <div className="space-y-2 py-2">
                <div className="h-4 bg-surface-2 dark:bg-dark-2 rounded animate-pulse" />
                <div className="h-4 bg-surface-2 dark:bg-dark-2 rounded animate-pulse w-5/6" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Stats list */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 bg-surface-1 dark:bg-dark-2 rounded-xl">
                    <Star className="w-4 h-4 text-ink-muted dark:text-dark-muted mx-auto mb-1" />
                    <p className="text-xs text-ink-faint dark:text-dark-faint">Stars</p>
                    <p className="text-lg font-bold text-ink dark:text-dark-ink mt-0.5 tabular-nums">
                      {gitStats.error ? '10+' : gitStats.stars}
                    </p>
                  </div>
                  <div className="p-3 bg-surface-1 dark:bg-dark-2 rounded-xl">
                    <GitFork className="w-4 h-4 text-ink-muted dark:text-dark-muted mx-auto mb-1" />
                    <p className="text-xs text-ink-faint dark:text-dark-faint">Forks</p>
                    <p className="text-lg font-bold text-ink dark:text-dark-ink mt-0.5 tabular-nums">
                      {gitStats.error ? '2+' : gitStats.forks}
                    </p>
                  </div>
                  <div className="p-3 bg-surface-1 dark:bg-dark-2 rounded-xl">
                    <AlertCircle className="w-4 h-4 text-ink-muted dark:text-dark-muted mx-auto mb-1" />
                    <p className="text-xs text-ink-faint dark:text-dark-faint">Issues</p>
                    <p className="text-lg font-bold text-ink dark:text-dark-ink mt-0.5 tabular-nums">
                      {gitStats.error ? '0' : gitStats.issues}
                    </p>
                  </div>
                </div>

                {/* Star & Fork buttons */}
                <div className="flex gap-2">
                  <a
                    href={`https://github.com/${GITHUB_REPO}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-accent text-white hover:bg-accent-hover transition-colors"
                  >
                    <Star className="w-3.5 h-3.5 fill-current" />
                    Star Repository
                  </a>
                  <a
                    href={`https://github.com/${GITHUB_REPO}/fork`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl border border-line dark:border-dark-line bg-surface-1 dark:bg-dark-2 hover:bg-surface-2 dark:hover:bg-dark-3 text-ink dark:text-dark-ink transition-colors"
                  >
                    <GitFork className="w-3.5 h-3.5" />
                    Fork Repo
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Rating Widget */}
        <div className="card bg-white dark:bg-dark-1 border-line dark:border-dark-line flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Star className="w-5 h-5 text-accent" />
              <h3 className="text-sm font-semibold text-ink dark:text-dark-ink">Rate this App</h3>
            </div>

            {/* Ratings Stat Overview */}
            {ratingStats.loading ? (
              <div className="h-6 bg-surface-2 dark:bg-dark-2 rounded animate-pulse mb-4" />
            ) : (
              <div className="flex items-baseline gap-2 mb-4">
                <span className="text-3xl font-extrabold text-ink dark:text-dark-ink tabular-nums">{ratingStats.average}</span>
                <span className="text-sm text-ink-muted dark:text-dark-muted">out of 5.0</span>
                <span className="text-xs text-ink-faint dark:text-dark-faint ml-1">
                  ({ratingStats.total} {ratingStats.total === 1 ? 'rating' : 'ratings'})
                </span>
              </div>
            )}

            {hasRated ? (
              <div className="bg-ok-light dark:bg-ok/10 border border-ok/20 rounded-xl p-4 text-center">
                <CheckCircle2 className="w-6 h-6 text-ok mx-auto mb-2" />
                <p className="text-sm font-semibold text-ok">Thank you for rating!</p>
                <p className="text-xs text-ink-muted dark:text-dark-muted mt-1">Your feedback helps improve everything-pesu.</p>
              </div>
            ) : (
              <form onSubmit={handleRatingSubmit} className="space-y-4">
                <p className="text-xs text-ink-muted dark:text-dark-muted">Select stars to leave feedback:</p>
                {/* Stars Selector */}
                <div className="flex items-center gap-1.5 py-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setUserRating(star)}
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      className="p-1 -m-1 focus:outline-none transition-transform active:scale-95 cursor-pointer"
                    >
                      <Star
                        className={`w-7 h-7 transition-colors ${
                          star <= (hoverRating || userRating)
                            ? 'text-accent fill-accent'
                            : 'text-line dark:text-dark-line'
                        }`}
                      />
                    </button>
                  ))}
                </div>

                {userRating > 0 && (
                  <div className="space-y-3 animate-fade-in">
                    <textarea
                      placeholder="Optional: What do you like or what can we improve? (max 500 chars)"
                      maxLength={500}
                      rows={3}
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                      className="w-full p-3 rounded-xl border border-line dark:border-dark-line bg-white dark:bg-dark-2 text-ink dark:text-dark-ink text-sm outline-none focus:border-accent"
                    />
                    <button
                      type="submit"
                      disabled={submittingRating}
                      className="w-full flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-white text-xs font-semibold disabled:opacity-50 transition-colors"
                    >
                      {submittingRating ? 'Submitting...' : 'Submit Rating'}
                    </button>
                  </div>
                )}
              </form>
            )}
          </div>
          
          <div className="border-t border-line dark:border-dark-line pt-3 mt-4 text-[11px] text-ink-faint dark:text-dark-faint flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5" />
            <span>Ratings are saved globally in Supabase / SQLite.</span>
          </div>
        </div>
      </div>

      {/* Row 2: Contact Form */}
      <div className="card bg-white dark:bg-dark-1 border-line dark:border-dark-line">
        <div className="flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 text-accent" />
          <h3 className="text-sm font-semibold text-ink dark:text-dark-ink">Contact Developer / Support</h3>
        </div>
        <p className="text-xs text-ink-muted dark:text-dark-muted mb-4">
          Have any bugs, issues, or suggestions? Submit this contact form and we will get back to you. A copy of your response will be sent to the email address provided.
        </p>

        {contactSuccess ? (
          <div className="bg-ok-light dark:bg-ok/10 border border-ok/20 rounded-xl p-6 text-center animate-fade-in">
            <CheckCircle2 className="w-8 h-8 text-ok mx-auto mb-2" />
            <p className="text-sm font-semibold text-ok">Message Sent Successfully!</p>
            <p className="text-xs text-ink-muted dark:text-dark-muted mt-1">We have received your inquiry. Check your email for a copy of the response.</p>
            <button
              onClick={() => setContactSuccess(false)}
              className="mt-4 px-4 py-2 rounded-xl bg-surface-2 dark:bg-dark-2 text-ink dark:text-dark-ink text-xs font-semibold hover:bg-surface-3 dark:hover:bg-dark-3 transition-colors"
            >
              Send Another Message
            </button>
          </div>
        ) : (
          <form onSubmit={handleContactSubmit} className="space-y-3">
            {contactError && (
              <div className="p-3 bg-bad-light dark:bg-bad/10 border border-bad/20 rounded-xl text-bad text-xs">
                {contactError}
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-ink-faint dark:text-dark-faint uppercase tracking-wider mb-1">Your Name</label>
                <input
                  type="text"
                  placeholder="Enter name"
                  required
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-line dark:border-dark-line bg-white dark:bg-dark-2 text-ink dark:text-dark-ink text-sm outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-ink-faint dark:text-dark-faint uppercase tracking-wider mb-1">Your Email</label>
                <input
                  type="email"
                  placeholder="name@example.com"
                  required
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-line dark:border-dark-line bg-white dark:bg-dark-2 text-ink dark:text-dark-ink text-sm outline-none focus:border-accent"
                />
              </div>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-ink-faint dark:text-dark-faint uppercase tracking-wider mb-1">Message</label>
              <textarea
                placeholder="Write your query or feedback here..."
                required
                rows={4}
                value={contactForm.message}
                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                className="w-full p-3 rounded-xl border border-line dark:border-dark-line bg-white dark:bg-dark-2 text-ink dark:text-dark-ink text-sm outline-none focus:border-accent"
              />
            </div>
            <button
              type="submit"
              disabled={submittingContact}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-white text-xs font-semibold disabled:opacity-50 transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              {submittingContact ? 'Sending...' : 'Send Message'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
