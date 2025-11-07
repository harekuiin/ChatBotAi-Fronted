import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, MessageSquare, TrendingUp, Users, Heart } from 'lucide-react'

function Dashboard({ setIsAuthenticated }) {
  const [userName, setUserName] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    // obtener nombre del usuario
    const name = localStorage.getItem('userName') || localStorage.getItem('userEmail') || 'Usuario'
    setUserName(name)
  }, [])

  const handleLogout = () => {
    // limpiar todo y cerrar sesion
    localStorage.removeItem('authToken')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    setIsAuthenticated(false)
    navigate('/login')
  }

  const stats = [
    {
      name: 'Consultas Realizadas',
      value: '0',
      icon: MessageSquare,
      color: 'bg-primary-600'
    },
    {
      name: 'Riesgo Evaluado',
      value: '0',
      icon: TrendingUp,
      color: 'bg-health-600'
    },
    {
      name: 'Recomendaciones',
      value: '0',
      icon: Heart,
      color: 'bg-red-600'
    }
  ]

  const quickActions = [
    {
      title: 'Abrir Chatbot',
      description: 'Consulta con el asistente de salud IA',
      icon: MessageSquare,
      color: 'bg-primary-600',
      action: () => navigate('/chatbot')
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50 fade-in">
      {/* Header */}
      <header className="bg-white shadow-sm border-b slide-up">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500">Bienvenido, {userName}</p>
            </div>
            <button
              onClick={handleLogout}
              className="btn-secondary flex items-center space-x-2"
            >
              <LogOut className="h-5 w-5" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div key={index} className="card slide-up" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  </div>
                  <div className={`${stat.color} p-3 rounded-lg`}>
                    <Icon className="h-8 w-8 text-white" />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quickActions.map((action, index) => {
              const Icon = action.icon
              return (
                <div
                  key={index}
                  onClick={action.action}
                  className="card cursor-pointer hover:scale-105 transition-transform duration-300 slide-in-right"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className={`${action.color} p-4 rounded-lg w-fit mb-4`}>
                    <Icon className="h-8 w-8 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{action.title}</h3>
                  <p className="text-sm text-gray-600">{action.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard

