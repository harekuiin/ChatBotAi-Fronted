import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, ArrowLeft, Bot, User, Loader2 } from 'lucide-react'
import axios from 'axios'

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '¡Hola! Soy tu asistente de salud. Puedo ayudarte con preguntas sobre riesgo cardiometabólico, datos NHANES, prevención y recomendaciones de salud. ¿En qué puedo ayudarte?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const navigate = useNavigate()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // verificar si hay mensaje de emergencia
  useEffect(() => {
    const emergencyMessage = localStorage.getItem('emergencyMessage')
    if (emergencyMessage) {
      localStorage.removeItem('emergencyMessage')
      
      // enviar automaticamente
      setTimeout(() => {
        const userMessage = {
          role: 'user',
          content: emergencyMessage
        }
        
        setMessages(prev => [...prev, userMessage])
        setLoading(true)
        
        // llamar al backend usando el nuevo endpoint
        const conversationId = localStorage.getItem('conversationId') || `user-${Date.now()}`
        
        axios.post('/api/chat', {
          question: emergencyMessage,
          conversation_id: conversationId
        }, {
          timeout: 30000
        })
        .then(response => {
          const assistantMessage = {
            role: 'assistant',
            content: response.data.answer
          }
          
          if (response.data.conversation_id) {
            localStorage.setItem('conversationId', response.data.conversation_id)
          } else {
            localStorage.setItem('conversationId', conversationId)
          }
          
          setMessages(prev => [...prev, assistantMessage])
        })
        .catch(error => {
          console.error('error enviando emergencia:', error)
          const errorMessage = {
            role: 'assistant',
            content: '⚠️ No se pudo conectar. Llama al 911 si es emergencia real.'
          }
          setMessages(prev => [...prev, errorMessage])
        })
        .finally(() => {
          setLoading(false)
        })
      }, 500)
    }
  }, [])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = {
      role: 'user',
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // usar el nuevo endpoint del backend
      const conversationId = localStorage.getItem('conversationId') || `user-${Date.now()}`
      
      const response = await axios.post('/api/chat', {
        question: userMessage.content,
        conversation_id: conversationId
      }, {
        timeout: 30000
      })

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer
      }

      if (response.data.conversation_id) {
        localStorage.setItem('conversationId', response.data.conversation_id)
      } else {
        localStorage.setItem('conversationId', conversationId)
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('error enviando:', error)
      
      let errorContent = 'Hubo un error procesando tu mensaje.'
      
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        errorContent = '⚠️ No se pudo conectar. Verifica que el backend este en http://localhost:8000'
      } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorContent = '⏱️ Tardo mucho. Intenta de nuevo.'
      } else if (error.response) {
        if (error.response.status === 401) {
          errorContent = '🔐 Error de auth. Inicia sesion de nuevo.'
        } else if (error.response.status === 500) {
          errorContent = '❌ Error en servidor. Intenta mas tarde.'
        } else {
          errorContent = `❌ Error ${error.response.status}: ${error.response.data?.detail || error.response.data?.message || 'desconocido'}`
        }
      } else if (error.request) {
        errorContent = '⚠️ No hay respuesta del servidor.'
      }
      
      const errorMessage = {
        role: 'assistant',
        content: errorContent
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col fade-in">
      {/* Header */}
      <header className="bg-white shadow-sm border-b slide-up">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Asistente de Salud IA</h1>
                <p className="text-xs text-gray-500">Basado en datos NHANES</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`flex items-start space-x-3 max-w-3xl ${
                  message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-transform duration-300 hover:scale-110 ${
                    message.role === 'user'
                      ? 'bg-primary-600'
                      : 'bg-gray-200'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="h-5 w-5 text-white" />
                  ) : (
                    <Bot className="h-5 w-5 text-gray-600" />
                  )}
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 transition-all duration-300 hover:shadow-md ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-900 shadow-sm border border-gray-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start fade-in">
              <div className="flex items-start space-x-3 max-w-3xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center pulse-soft">
                  <Bot className="h-5 w-5 text-gray-600" />
                </div>
                <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-200">
                  <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <form onSubmit={handleSend} className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend(e)
                  }
                }}
                placeholder="Escribe tu pregunta sobre salud cardiometabólica..."
                rows={1}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none transition-all duration-300 hover:border-primary-300"
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
          <p className="mt-2 text-xs text-gray-500 text-center">
            Este asistente proporciona información educativa. No reemplaza el consejo médico profesional.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Chatbot

