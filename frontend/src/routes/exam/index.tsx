import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import {
  FileQuestion,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  BookOpen,
} from 'lucide-react'

export const Route = createFileRoute('/exam/')({
  component: ExamPage,
})

type ExamState = 'setup' | 'generating' | 'taking' | 'grading' | 'feedback'

interface Question {
  id: string
  text: string
  options: { id: string; text: string }[]
  targetSkill: string
}

interface ExamPrompt {
  title: string
  description: string
  questions: Question[]
}

interface ExamSubmission {
  questionId: string
  selectedOptionId: string
}

interface QuestionFeedback {
  questionId: string
  isCorrect: boolean
  correctOptionId: string
  explanation: string
  skillImpact: {
    skill: string
    change: 'improved' | 'needs_review'
    nextReviewDate: string
  }
}

interface ExamGradingResult {
  score: number
  total: number
  feedback: QuestionFeedback[]
  overallFeedback: string
}

const MOCK_EXAM_PROMPT: ExamPrompt = {
  title: 'Targeted Review: Pretérito vs. Imperfecto',
  description:
    'This exam focuses on your weakest areas identified in recent tasks.',
  questions: [
    {
      id: 'q1',
      text: 'Ayer, yo ___ a la tienda a comprar pan.',
      options: [
        { id: 'o1', text: 'iba' },
        { id: 'o2', text: 'fui' },
        { id: 'o3', text: 'iré' },
        { id: 'o4', text: 'yendo' },
      ],
      targetSkill: 'Pretérito Indefinido',
    },
    {
      id: 'q2',
      text: 'Cuando era niño, siempre ___ en el parque.',
      options: [
        { id: 'o1', text: 'jugué' },
        { id: 'o2', text: 'jugaba' },
        { id: 'o3', text: 'juego' },
        { id: 'o4', text: 'jugaré' },
      ],
      targetSkill: 'Pretérito Imperfecto',
    },
    {
      id: 'q3',
      text: 'Nosotros ___ la televisión cuando sonó el teléfono.',
      options: [
        { id: 'o1', text: 'miramos' },
        { id: 'o2', text: 'mirábamos' },
        { id: 'o3', text: 'miraremos' },
        { id: 'o4', text: 'mirando' },
      ],
      targetSkill: 'Pretérito Imperfecto',
    },
  ],
}

const MOCK_EXAM_GRADING: ExamGradingResult = {
  score: 2,
  total: 3,
  overallFeedback:
    'Good effort! You are improving on the Indefinido, but still need some work on identifying when an action is interrupted (Imperfecto).',
  feedback: [
    {
      questionId: 'q1',
      isCorrect: true,
      correctOptionId: 'o2',
      explanation:
        '"Fui" is correct because the action (going to the store) was completed at a specific point in the past ("Ayer").',
      skillImpact: {
        skill: 'Pretérito Indefinido',
        change: 'improved',
        nextReviewDate: 'in 7 days (Spaced Repetition)',
      },
    },
    {
      questionId: 'q2',
      isCorrect: true,
      correctOptionId: 'o2',
      explanation:
        '"Jugaba" is correct for describing habitual actions in the past ("Cuando era niño, siempre...").',
      skillImpact: {
        skill: 'Pretérito Imperfecto',
        change: 'improved',
        nextReviewDate: 'in 5 days (Spaced Repetition)',
      },
    },
    {
      questionId: 'q3',
      isCorrect: false,
      correctOptionId: 'o2',
      explanation:
        '"Mirábamos" is correct. The action of watching TV was ongoing (Imperfecto) when it was interrupted by the phone ringing (Indefinido - "sonó").',
      skillImpact: {
        skill: 'Pretérito Imperfecto (Interrupted Actions)',
        change: 'needs_review',
        nextReviewDate: 'Tomorrow (Spaced Repetition)',
      },
    },
  ],
}

function ExamPage() {
  const [examState, setExamState] = useState<ExamState>('setup')
  const [examPrompt, setExamPrompt] = useState<ExamPrompt | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [gradingResult, setGradingResult] = useState<ExamGradingResult | null>(
    null,
  )

  const handleGenerateExam = async () => {
    setExamState('generating')
    // Simulate API call to LLM
    setTimeout(() => {
      setExamPrompt(MOCK_EXAM_PROMPT)
      setExamState('taking')
    }, 2000)
  }

  const handleSelectAnswer = (questionId: string, optionId: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }))
  }

  const handleSubmitExam = async () => {
    setExamState('grading')
    // Simulate API call to grade answers
    setTimeout(() => {
      // In a real app, we'd send 'answers' to the backend
      setGradingResult(MOCK_EXAM_GRADING)
      setExamState('feedback')
    }, 2500)
  }

  const handleReset = () => {
    setExamState('setup')
    setExamPrompt(null)
    setAnswers({})
    setGradingResult(null)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6 md:p-8 max-w-4xl mx-auto">
      {/* VIEW 1: SETUP */}
      {examState === 'setup' && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 mb-2">
              Targeted Practice Exam
            </h2>
            <p className="text-slate-600 text-lg">
              Generate a custom multiple-choice exam focusing on your weakest
              skills to strengthen your foundation.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 mb-6">
              <FileQuestion className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold mb-4">
              Ready to test your knowledge?
            </h3>
            <p className="text-slate-500 mb-8 max-w-md mx-auto">
              We'll analyze your past performance and generate 3-5 targeted
              questions.
            </p>
            <button
              onClick={handleGenerateExam}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-8 py-3 rounded-xl shadow-sm transition-colors flex items-center gap-2 mx-auto"
            >
              Generate Custom Exam <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* VIEW 2: GENERATING */}
      {examState === 'generating' && (
        <div className="flex flex-col items-center justify-center py-32 space-y-6 animate-in fade-in duration-300">
          <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
          <div className="text-center">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              Generating Your Exam
            </h2>
            <p className="text-slate-500">
              Analyzing weak points and crafting targeted questions...
            </p>
          </div>
        </div>
      )}

      {/* VIEW 3: TAKING EXAM */}
      {examState === 'taking' && examPrompt && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              {examPrompt.title}
            </h2>
            <p className="text-slate-600">{examPrompt.description}</p>
          </div>

          <div className="space-y-6">
            {examPrompt.questions.map((q, idx) => (
              <div
                key={q.id}
                className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-medium text-slate-800">
                    <span className="text-indigo-600 font-bold mr-2">
                      Q{idx + 1}.
                    </span>
                    {q.text}
                  </h3>
                  <span className="text-xs font-medium px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
                    {q.targetSkill}
                  </span>
                </div>

                <div className="space-y-3">
                  {q.options.map((opt) => (
                    <label
                      key={opt.id}
                      className={`flex items-center p-4 rounded-xl border cursor-pointer transition-colors ${
                        answers[q.id] === opt.id
                          ? 'bg-indigo-50 border-indigo-300 ring-1 ring-indigo-300'
                          : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${q.id}`}
                        value={opt.id}
                        checked={answers[q.id] === opt.id}
                        onChange={() => handleSelectAnswer(q.id, opt.id)}
                        className="w-5 h-5 text-indigo-600 border-slate-300 focus:ring-indigo-600"
                      />
                      <span className="ml-3 text-slate-700 font-medium">
                        {opt.text}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={handleSubmitExam}
              disabled={
                Object.keys(answers).length !== examPrompt.questions.length
              }
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium px-8 py-3 rounded-xl shadow-sm transition-colors flex items-center gap-2"
            >
              Submit Exam
            </button>
          </div>
        </div>
      )}

      {/* VIEW 4: GRADING */}
      {examState === 'grading' && (
        <div className="flex flex-col items-center justify-center py-32 space-y-6 animate-in fade-in duration-300">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
            <CheckCircle className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-indigo-400 opacity-50" />
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              Grading Exam
            </h2>
            <p className="text-slate-500">
              Evaluating answers and updating spaced repetition schedule...
            </p>
          </div>
        </div>
      )}

      {/* VIEW 5: FEEDBACK */}
      {examState === 'feedback' && gradingResult && examPrompt && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div
              className={`p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 justify-between ${gradingResult.score === gradingResult.total ? 'bg-emerald-50' : 'bg-indigo-50'}`}
            >
              <div>
                <div className="flex items-center gap-3 mb-2">
                  {gradingResult.score === gradingResult.total ? (
                    <CheckCircle className="text-emerald-600 w-8 h-8" />
                  ) : (
                    <TrendingUp className="text-indigo-600 w-8 h-8" />
                  )}
                  <h2
                    className={`text-3xl font-bold ${gradingResult.score === gradingResult.total ? 'text-emerald-900' : 'text-indigo-900'}`}
                  >
                    Score: {gradingResult.score}/{gradingResult.total}
                  </h2>
                </div>
              </div>
              <div className="max-w-md">
                <p
                  className={`text-sm ${gradingResult.score === gradingResult.total ? 'text-emerald-800/80' : 'text-indigo-800/80'}`}
                >
                  {gradingResult.overallFeedback}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <h3 className="text-xl font-bold text-slate-800 px-2">
              Detailed Review
            </h3>
            {gradingResult.feedback.map((fb, idx) => {
              const question = examPrompt.questions.find(
                (q) => q.id === fb.questionId,
              )!
              const selectedOpt = question.options.find(
                (o) => o.id === answers[fb.questionId],
              )
              const correctOpt = question.options.find(
                (o) => o.id === fb.correctOptionId,
              )

              return (
                <div
                  key={fb.questionId}
                  className={`bg-white p-6 rounded-2xl shadow-sm border ${fb.isCorrect ? 'border-emerald-200' : 'border-rose-200'}`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-lg font-medium text-slate-800">
                      <span
                        className={`${fb.isCorrect ? 'text-emerald-600' : 'text-rose-600'} font-bold mr-2`}
                      >
                        Q{idx + 1}.
                      </span>
                      {question.text}
                    </h4>
                    {fb.isCorrect ? (
                      <span className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-md">
                        <CheckCircle className="w-3 h-3" /> Correct
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-100 px-2 py-1 rounded-md">
                        <XCircle className="w-3 h-3" /> Incorrect
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
                        Your Answer
                      </span>
                      <p
                        className={`font-medium ${fb.isCorrect ? 'text-emerald-700' : 'text-rose-700'}`}
                      >
                        {selectedOpt?.text || 'No answer'}
                      </p>
                    </div>
                    {!fb.isCorrect && (
                      <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4">
                        <span className="text-xs font-bold text-emerald-800/60 uppercase tracking-wider block mb-2">
                          Correct Answer
                        </span>
                        <p className="text-emerald-900 font-medium">
                          {correctOpt?.text}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-600 flex gap-3 items-start border border-slate-100 mb-4">
                    <BookOpen className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                    <p>{fb.explanation}</p>
                  </div>

                  <div className="flex items-center gap-2 pt-4 border-t border-slate-100">
                    <RefreshCw className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-medium text-slate-700">
                      Spaced Repetition:
                    </span>
                    <span className="text-sm text-slate-600">
                      {fb.skillImpact.skill} &rarr;{' '}
                      <span className="font-semibold text-indigo-700">
                        Review {fb.skillImpact.nextReviewDate}
                      </span>
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex justify-center pt-8 pb-12">
            <Link
              to="/"
              className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium px-6 py-3 rounded-xl transition-colors border border-indigo-200 inline-flex items-center gap-2"
            >
              Return to Dashboard
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
