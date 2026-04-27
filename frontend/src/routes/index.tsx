import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Link } from '@tanstack/react-router'
import {
  BookOpen,
  Edit3,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  PlayCircle,
  FileQuestion,
} from 'lucide-react'

export const Route = createFileRoute('/')({ component: App })

// --- MOCK DATA & TYPES ---

type AppState =
  | 'select-task'
  | 'generating'
  | 'writing'
  | 'grading'
  | 'feedback'

interface SkillTag {
  id: string
  name: string
  score: number
  category: string
}

const mockSkills: SkillTag[] = [
  { id: '1', name: 'Pretérito Indefinido', score: 45, category: 'Grammar' },
  { id: '2', name: 'Pretérito Imperfecto', score: 50, category: 'Grammar' },
  {
    id: '3',
    name: 'Vocabulary: Work/Study',
    score: 65,
    category: 'Vocabulary',
  },
  { id: '4', name: 'Connectors', score: 80, category: 'Cohesion' },
]

interface GeneratedPrompt {
  taskType: string
  scenario: string
  bulletPoints: string[]
  targetSkills: string[]
}

const mockPrompt1: GeneratedPrompt = {
  taskType: 'Task 1: Email',
  scenario:
    'Write an email to a friend telling them about a recent trip you took.',
  bulletPoints: [
    'Where did you go and when?',
    'What did you do there? (Use Pretérito Indefinido)',
    'What was the place like? (Use Pretérito Imperfecto)',
    'Suggest a plan to meet and show them photos.',
  ],
  targetSkills: ['Pretérito Indefinido', 'Pretérito Imperfecto'],
}

const mockPrompt2: GeneratedPrompt = {
  taskType: 'Task 2: Narrative',
  scenario: 'Write a short story about your first day at a new job or school.',
  bulletPoints: [
    'Describe the setting and how you felt. (Use Pretérito Imperfecto)',
    'Explain what happened during the day. (Use Pretérito Indefinido)',
    'Mention who you met and what they were like.',
    'Say how the day ended.',
  ],
  targetSkills: [
    'Pretérito Indefinido',
    'Pretérito Imperfecto',
    'Vocabulary: Work/Study',
  ],
}

interface InlineCorrection {
  original: string
  correction: string
  explanation: string
}

interface GradingResult {
  score: number // 0-3
  verdict: 'Pass' | 'Fail'
  corrections: InlineCorrection[]
  succeededTags: string[]
  failedTags: string[]
  overallFeedback: string
}

const mockGrading: GradingResult = {
  score: 2,
  verdict: 'Pass',
  corrections: [
    {
      original: 'El hotel era muy bonito y tuvo una piscina.',
      correction: 'El hotel era muy bonito y tenía una piscina.',
      explanation:
        'Use Pretérito Imperfecto ("tenía") for descriptions in the past, not Indefinido ("tuvo").',
    },
    {
      original: 'Yo fui al playa todos los días.',
      correction: 'Yo fui a la playa todos los días.',
      explanation:
        '"Playa" is feminine, so use "a la" instead of "al" (a + el).',
    },
  ],
  succeededTags: ['Pretérito Indefinido'],
  failedTags: ['Pretérito Imperfecto'],
  overallFeedback:
    'Good effort! You successfully used the Pretérito Indefinido to narrate events, but remember to use the Pretérito Imperfecto for descriptions in the past.',
}

// --- APP COMPONENT ---

function App() {
  const [appState, setAppState] = useState<AppState>('select-task')
  const [selectedTask, setSelectedTask] = useState<string | null>(null)
  const [prompt, setPrompt] = useState<GeneratedPrompt | null>(null)
  const [submission, setSubmission] = useState('')
  const [grading, setGrading] = useState<GradingResult | null>(null)

  const [token, setToken] = useState<string | null>(null)
  const [skills, setSkills] = useState<SkillTag[]>([])

  const fetchSkills = async (currentToken: string) => {
    try {
      const skillsRes = await fetch('/api/skills/', {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      const skillsData = await skillsRes.json()
      setSkills(skillsData)
    } catch (err) {
      console.error('Failed to fetch skills', err)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        const formData = new URLSearchParams()
        formData.append('username', import.meta.env.VITE_TEST_USER_EMAIL || 'test@example.com')
        formData.append('password', import.meta.env.VITE_TEST_USER_PASSWORD || 'password123')

        const loginRes = await fetch('/api/auth/login', {
          method: 'POST',
          body: formData,
        })
        const loginData = await loginRes.json()
        const accessToken = loginData.access_token
        setToken(accessToken)

        await fetchSkills(accessToken)
      } catch (err) {
        console.error('Failed to initialize login', err)
      }
    }
    init()
  }, [])

  const handleTaskSelect = async (task: string) => {
    setSelectedTask(task)
    setAppState('generating')

    try {
      const res = await fetch('/api/tasks/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ taskType: task }),
      })
      const data = await res.json()
      setPrompt(data)
      setAppState('writing')
    } catch (err) {
      console.error(err)
      setAppState('select-task')
    }
  }

  const handleSubmit = async () => {
    setAppState('grading')

    try {
      const res = await fetch('/api/tasks/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ submission, prompt }),
      })
      const data = await res.json()
      setGrading(data)
      setAppState('feedback')
    } catch (err) {
      console.error(err)
      setAppState('writing')
    }
  }

  const handleReset = () => {
    setAppState('select-task')
    setSelectedTask(null)
    setPrompt(null)
    setSubmission('')
    setGrading(null)

    if (token) {
      fetchSkills(token)
    }
  }

  const wordCount = submission
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <main className="max-w-4xl mx-auto p-6 md:p-8">
        {/* VIEW 1: SELECT TASK */}
        {appState === 'select-task' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-3xl font-bold text-slate-800 mb-2">
                Welcome back!
              </h2>
              <p className="text-slate-600 text-lg">
                Let's focus on improving your lowest-scoring skills.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="text-amber-500 w-5 h-5" />
                Current Weaknesses
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.isArray(skills) &&
                  skills
                    .filter((s) => s.score <= 65)
                    .map((skill) => (
                      <div
                        key={skill.id}
                        className="p-4 rounded-xl bg-slate-50 border border-slate-100"
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium text-slate-700">
                            {skill.name}
                          </span>
                          <span className="text-sm font-bold text-amber-600">
                            {skill.score}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div
                            className="bg-amber-500 h-2 rounded-full"
                            style={{ width: `${skill.score}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
              </div>
            </div>

            <div>
              <h3 className="text-xl font-bold mb-4">Select a Practice Task</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <button
                  onClick={() => handleTaskSelect('Task 1: Email')}
                  className="text-left bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-indigo-100 p-3 rounded-lg text-indigo-600">
                      <Edit3 className="w-6 h-6" />
                    </div>
                    <ChevronRight className="text-slate-400 group-hover:text-indigo-600 transition-colors" />
                  </div>
                  <h4 className="text-lg font-bold mb-2">
                    Task 1: Email / Message
                  </h4>
                  <p className="text-slate-500 text-sm mb-4">
                    Write a short correspondence (60-70 words) based on a
                    prompt.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
                      Grammar Focus
                    </span>
                    <span className="text-xs font-medium px-2 py-1 bg-amber-50 text-amber-700 rounded-md border border-amber-200">
                      Pretérito Indefinido
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => handleTaskSelect('Task 2: Narrative')}
                  className="text-left bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-indigo-100 p-3 rounded-lg text-indigo-600">
                      <PlayCircle className="w-6 h-6" />
                    </div>
                    <ChevronRight className="text-slate-400 group-hover:text-indigo-600 transition-colors" />
                  </div>
                  <h4 className="text-lg font-bold mb-2">
                    Task 2: Narrative / Opinion
                  </h4>
                  <p className="text-slate-500 text-sm mb-4">
                    Write a descriptive text or story (70-80 words).
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
                      Grammar & Vocab Focus
                    </span>
                    <span className="text-xs font-medium px-2 py-1 bg-amber-50 text-amber-700 rounded-md border border-amber-200">
                      Pretérito Imperfecto
                    </span>
                  </div>
                </button>

                <Link
                  to="/exam"
                  className="text-left bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group block col-span-1 md:col-span-2"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-indigo-100 p-3 rounded-lg text-indigo-600">
                      <FileQuestion className="w-6 h-6" />
                    </div>
                    <ChevronRight className="text-slate-400 group-hover:text-indigo-600 transition-colors" />
                  </div>
                  <h4 className="text-lg font-bold mb-2">
                    Mock Exam: Multiple Choice
                  </h4>
                  <p className="text-slate-500 text-sm mb-4">
                    Take a personalized multiple-choice exam targeting your weakest points and unexplored skills. Spaced repetition included!
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
                      Targeted Practice
                    </span>
                    <span className="text-xs font-medium px-2 py-1 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-200">
                      Spaced Repetition
                    </span>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: GENERATING PROMPT */}
        {appState === 'generating' && (
          <div className="flex flex-col items-center justify-center py-20 space-y-6 animate-in fade-in duration-300">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
            <div className="text-center">
              <h2 className="text-2xl font-bold text-slate-800 mb-2">
                Generating Custom Prompt
              </h2>
              <p className="text-slate-500">
                Tailoring {selectedTask} to target your weak skills...
              </p>
            </div>
          </div>
        )}

        {/* VIEW 3: WRITING */}
        {appState === 'writing' && prompt && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
              <button
                onClick={handleReset}
                className="hover:text-indigo-600 transition-colors"
              >
                Tasks
              </button>
              <ChevronRight className="w-4 h-4" />
              <span className="font-medium text-slate-800">
                {prompt.taskType}
              </span>
            </div>

            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6">
              <h3 className="text-indigo-900 font-bold text-lg mb-2">
                Prompt Scenario
              </h3>
              <p className="text-indigo-800 mb-4">{prompt.scenario}</p>

              <ul className="space-y-2 mb-4">
                {prompt.bulletPoints.map((bp, idx) => (
                  <li key={idx} className="flex gap-3 text-indigo-800/80">
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full mt-2 shrink-0"></div>
                    <span>{bp}</span>
                  </li>
                ))}
              </ul>

              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-indigo-200/50">
                <span className="text-xs font-bold text-indigo-900/60 uppercase tracking-wider">
                  Targeted Skills:
                </span>
                <div className="flex gap-2">
                  {prompt.targetSkills.map((skill) => (
                    <span
                      key={skill}
                      className="text-xs font-medium px-2 py-1 bg-white text-indigo-700 rounded-md shadow-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
              <div className="bg-slate-50 border-b border-slate-200 p-3 flex justify-between items-center text-sm text-slate-500">
                <span>Your Response</span>
                <span
                  className={`font-medium ${wordCount < 60 ? 'text-amber-600' : 'text-emerald-600'}`}
                >
                  {wordCount} words{' '}
                  <span className="text-slate-400 font-normal">
                    (Target: 60-80)
                  </span>
                </span>
              </div>
              <textarea
                value={submission}
                onChange={(e) => setSubmission(e.target.value)}
                placeholder="Escribe tu respuesta aquí..."
                className="w-full h-64 p-4 md:p-6 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset text-lg text-slate-700 leading-relaxed"
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSubmit}
                disabled={submission.trim().length === 0}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium px-8 py-3 rounded-xl shadow-sm transition-colors flex items-center gap-2"
              >
                Submit for Grading
              </button>
            </div>
          </div>
        )}

        {/* VIEW 4: GRADING */}
        {appState === 'grading' && (
          <div className="flex flex-col items-center justify-center py-20 space-y-6 animate-in fade-in duration-300">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
              <CheckCircle className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-indigo-400 opacity-50" />
            </div>
            <div className="text-center">
              <h2 className="text-2xl font-bold text-slate-800 mb-2">
                Analyzing Submission
              </h2>
              <p className="text-slate-500">
                Evaluating Coherence, Fluency, Correctness, and Scope...
              </p>
            </div>
          </div>
        )}

        {/* VIEW 5: FEEDBACK */}
        {appState === 'feedback' && grading && prompt && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Top Score Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div
                className={`p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 justify-between ${grading.verdict === 'Pass' ? 'bg-emerald-50' : 'bg-rose-50'}`}
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    {grading.verdict === 'Pass' ? (
                      <CheckCircle className="text-emerald-600 w-8 h-8" />
                    ) : (
                      <XCircle className="text-rose-600 w-8 h-8" />
                    )}
                    <h2
                      className={`text-3xl font-bold ${grading.verdict === 'Pass' ? 'text-emerald-900' : 'text-rose-900'}`}
                    >
                      {grading.verdict}
                    </h2>
                  </div>
                  <p
                    className={`text-lg font-medium ${grading.verdict === 'Pass' ? 'text-emerald-700' : 'text-rose-700'}`}
                  >
                    DELE Score: {grading.score} / 3
                  </p>
                </div>

                <div className="max-w-md">
                  <p
                    className={`text-sm ${grading.verdict === 'Pass' ? 'text-emerald-800/80' : 'text-rose-800/80'}`}
                  >
                    {grading.overallFeedback}
                  </p>
                </div>
              </div>
            </div>

            {/* Skill Tracking Update */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <TrendingUp className="text-emerald-500 w-5 h-5" />
                  Skills Improved
                </h3>
                <ul className="space-y-3">
                  {grading.succeededTags.map((tag) => (
                    <li
                      key={tag}
                      className="flex justify-between items-center p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl"
                    >
                      <span className="font-medium text-emerald-800">
                        {tag}
                      </span>
                      <span className="text-xs font-bold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-md">
                        +5%
                      </span>
                    </li>
                  ))}
                  {grading.succeededTags.length === 0 && (
                    <p className="text-slate-500 text-sm">
                      No specific target skills fully mastered this time.
                    </p>
                  )}
                </ul>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <AlertTriangle className="text-amber-500 w-5 h-5" />
                  Needs More Practice
                </h3>
                <ul className="space-y-3">
                  {grading.failedTags.map((tag) => (
                    <li
                      key={tag}
                      className="flex justify-between items-center p-3 bg-amber-50/50 border border-amber-100 rounded-xl"
                    >
                      <span className="font-medium text-amber-800">{tag}</span>
                      <span className="text-xs font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded-md">
                        -2%
                      </span>
                    </li>
                  ))}
                  {grading.failedTags.length === 0 && (
                    <p className="text-slate-500 text-sm">
                      Great job, no critical failures in target skills!
                    </p>
                  )}
                </ul>
              </div>
            </div>

            {/* Inline Corrections */}
            <div>
              <h3 className="text-xl font-bold text-slate-800 mb-4">
                Detailed Corrections
              </h3>
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden divide-y divide-slate-100">
                {grading.corrections.map((corr, idx) => (
                  <div key={idx} className="p-4 md:p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                      <div className="bg-rose-50/50 border border-rose-100 rounded-xl p-4">
                        <span className="text-xs font-bold text-rose-800/60 uppercase tracking-wider block mb-2">
                          Original
                        </span>
                        <p className="text-rose-900 line-through decoration-rose-300 decoration-2">
                          {corr.original}
                        </p>
                      </div>
                      <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4">
                        <span className="text-xs font-bold text-emerald-800/60 uppercase tracking-wider block mb-2">
                          Correction
                        </span>
                        <p className="text-emerald-900 font-medium">
                          {corr.correction}
                        </p>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600 flex gap-2 items-start border border-slate-100">
                      <BookOpen className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                      <p>{corr.explanation}</p>
                    </div>
                  </div>
                ))}
                {grading.corrections.length === 0 && (
                  <div className="p-8 text-center text-slate-500">
                    No corrections needed! Your text was excellent.
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-center pt-4">
              <button
                onClick={handleReset}
                className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium px-6 py-3 rounded-xl transition-colors border border-indigo-200"
              >
                Return to Dashboard
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
