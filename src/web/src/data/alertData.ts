export interface FullDataItem {
  timestamp: string
  temperature: number
  humidity: number
  combustible_gas: number
  motion_detected: number
  predicted_occupied: number
  occupied_probability: number
}

export interface RealtimeData {
  timestamp: string
  temperature: number
  humidity: number
  gas: number
  current_motion: string
  predicted_future_15min: string
  confidence: number
}

export interface AlertItem {
  timestamp: string
  gas_value: number
  alert_level: number
}

export const generateFullData = (): FullDataItem[] => {
  const data: FullDataItem[] = []
  const baseTime = new Date('2026-06-11 18:16:55').getTime()
  
  for (let i = 0; i < 40; i++) {
    const time = new Date(baseTime + i * 900000)
    const temp = 26 + Math.sin(i * 0.3) * 4 + Math.random() * 1
    const humidity = 45 + Math.cos(i * 0.2) * 10 + Math.random() * 5
    const gas = 80 + Math.random() * 40
    const motion = Math.random() > 0.4 ? 1 : 0
    const predicted = motion === 1 ? 1 : Math.random() > 0.3 ? 1 : 0
    const probability = predicted === 1 ? 0.9 + Math.random() * 0.1 : 0.2 + Math.random() * 0.3
    
    data.push({
      timestamp: time.toISOString().replace('T', ' ').substring(0, 19),
      temperature: parseFloat(temp.toFixed(2)),
      humidity: parseFloat(humidity.toFixed(1)),
      combustible_gas: Math.round(gas),
      motion_detected: motion,
      predicted_occupied: predicted,
      occupied_probability: parseFloat(probability.toFixed(2))
    })
  }
  
  return data
}

export const realtimeData: RealtimeData = {
  timestamp: '2026-06-11 19:16:51',
  temperature: 30.9,
  humidity: 36.6,
  gas: 119,
  current_motion: '有人',
  predicted_future_15min: '无人',
  confidence: 22.0
}

export const generateAlerts = (): AlertItem[] => {
  const alerts: AlertItem[] = []
  const baseTime = new Date('2026-06-11 18:16:55').getTime()
  
  for (let i = 0; i < 20; i++) {
    const time = new Date(baseTime + i * 1800000)
    const gas_value = 90 + Math.random() * 30
    const alert_level = gas_value > 110 ? 1 : 2
    
    alerts.push({
      timestamp: time.toISOString().replace('T', ' ').substring(0, 19),
      gas_value: Math.round(gas_value),
      alert_level
    })
  }
  
  return alerts.reverse()
}

export const fullData = generateFullData()
export const alerts = generateAlerts()