import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, X, Heart, Droplet, Zap, Skull, Activity, Thermometer } from 'lucide-react'

function EmergencyButton() {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef(null)
  const navigate = useNavigate()

  // cerrar menu si click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const emergencyOptions = [
    {
      id: 'asfixia',
      title: 'Asfixia / Atragantamiento',
      icon: Activity,
      color: 'bg-red-600',
      message: 'Necesito ayuda inmediata por asfixia o atragantamiento. ¿Qué debo hacer?'
    },
    {
      id: 'paro-cardiaco',
      title: 'Paro Cardíaco',
      icon: Heart,
      color: 'bg-red-700',
      message: 'Hay una persona con posible paro cardíaco. ¿Cómo puedo ayudar con RCP?'
    },
    {
      id: 'hemorragia',
      title: 'Hemorragia Severa',
      icon: Droplet,
      color: 'bg-red-600',
      message: 'Hay una hemorragia severa. ¿Cómo puedo detener el sangrado?'
    },
    {
      id: 'quemadura',
      title: 'Quemaduras',
      icon: Thermometer,
      color: 'bg-orange-600',
      message: 'Hay una persona con quemaduras. ¿Qué primeros auxilios debo aplicar?'
    },
    {
      id: 'desmayo',
      title: 'Desmayo / Pérdida de Conciencia',
      icon: Skull,
      color: 'bg-purple-600',
      message: 'Alguien se ha desmayado o perdió la conciencia. ¿Qué debo hacer?'
    },
    {
      id: 'convulsion',
      title: 'Convulsiones',
      icon: Zap,
      color: 'bg-yellow-600',
      message: 'Hay una persona teniendo convulsiones. ¿Cómo puedo ayudar?'
    },
    {
      id: 'dolor-pecho',
      title: 'Dolor de Pecho Severo',
      icon: Activity,
      color: 'bg-red-600',
      message: 'Tengo dolor de pecho severo. ¿Podría ser un infarto? ¿Qué debo hacer?'
    }
  ]

  const handleEmergencyClick = (option) => {
    setIsOpen(false)
    
    // guardar mensaje de emergencia
    localStorage.setItem('emergencyMessage', option.message)
    
    // ir al chatbot
    navigate('/chatbot')
    
    // scroll al final para ver el mensaje
    setTimeout(() => {
      window.scrollTo(0, document.body.scrollHeight)
    }, 500)
  }

  return (
    <>
      {/* Botón flotante de emergencia */}
      <div className="fixed bottom-6 right-6 z-50" ref={menuRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`
            ${isOpen ? 'bg-red-700' : 'bg-red-600'} 
            hover:bg-red-700 
            text-white 
            rounded-full 
            p-4 
            shadow-2xl 
            transition-all 
            duration-300 
            transform 
            hover:scale-110 
            active:scale-95
            flex 
            items-center 
            justify-center
            ${isOpen ? 'rotate-45' : 'rotate-0'}
          `}
          style={{ width: '64px', height: '64px' }}
          aria-label="Botón de emergencia"
        >
          {isOpen ? (
            <X className="h-8 w-8" />
          ) : (
            <AlertTriangle className="h-8 w-8" />
          )}
        </button>

        {/* Menú de emergencias */}
        {isOpen && (
          <div className="absolute bottom-20 right-0 w-80 bg-white rounded-xl shadow-2xl shadow-red-500/50 p-4 space-y-2 animate-slide-up">
            <div className="text-center mb-3">
              <h3 className="font-bold text-gray-900 text-lg">Emergencias Médicas</h3>
              <p className="text-xs text-gray-500 mt-1">Selecciona el tipo de emergencia</p>
            </div>
            
            <div className="max-h-96 overflow-y-auto space-y-2">
              {emergencyOptions.map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.id}
                    onClick={() => handleEmergencyClick(option)}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-red-50 transition-colors duration-200 text-left border border-gray-200 hover:border-red-300"
                  >
                    <div className={`${option.color} p-2 rounded-lg flex-shrink-0`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <span className="text-sm font-medium text-gray-900 flex-1">
                      {option.title}
                    </span>
                  </button>
                )
              })}
            </div>

            <div className="mt-4 pt-3 border-t border-gray-200">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs text-red-800 font-semibold mb-1">
                  ⚠️ EMERGENCIA REAL
                </p>
                <p className="text-xs text-red-700">
                  Si es una emergencia real, llama inmediatamente a:
                </p>
                <a 
                  href="tel:911" 
                  className="text-lg font-bold text-red-600 hover:text-red-700 block mt-1"
                >
                  📞 911
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Overlay cuando el menú está abierto */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}

export default EmergencyButton

