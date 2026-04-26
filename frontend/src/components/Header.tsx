import { BookOpen, TrendingUp } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-2">
        <BookOpen className="text-indigo-600 w-6 h-6" />
        <h1 className="font-bold text-xl tracking-tight text-slate-800">
          DELE A2 Prep
        </h1>
      </div>
      <div className="flex items-center gap-4 text-sm font-medium text-slate-600">
        <span className="flex items-center gap-1">
          <TrendingUp className="w-4 h-4" /> Progress
        </span>
        <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold">
          A2
        </div>
      </div>
    </header>
  )
}
