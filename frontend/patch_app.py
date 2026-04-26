import re

with open('src/routes/index.tsx', 'r') as f:
    content = f.read()

replacement = """
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
        formData.append('username', 'test@example.com')
        formData.append('password', 'password123')

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
"""

pattern = re.compile(r'  // Simulation handlers\n  const handleTaskSelect.*?setGrading\(null\)\n  }', re.DOTALL)
new_content = pattern.sub(replacement.strip(), content)

with open('src/routes/index.tsx', 'w') as f:
    f.write(new_content)
