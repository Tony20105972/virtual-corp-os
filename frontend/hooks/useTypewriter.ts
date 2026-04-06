import { useState, useEffect } from "react"

export function useTypewriter(
  text: string,
  speed: number = 30,
  onComplete?: () => void,
) {
  const [displayed, setDisplayed] = useState("")
  const [done, setDone]           = useState(false)

  useEffect(() => {
    setDisplayed("")
    setDone(false)
    if (!text) return

    let i = 0
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) {
        clearInterval(timer)
        setDone(true)
        onComplete?.()
      }
    }, speed)

    return () => clearInterval(timer)
  }, [text, speed])   // text 변경 시 처음부터 재시작

  return { displayed, done }
}
