/**
 * 前端数据格式化工具
 * 统一所有传感器数值为小数点后一位
 */

/** 格式化数值为一位小数，非数字返回 '--' */
export const fmt1 = (val) => {
  if (val === null || val === undefined || val === '') return '--'
  const n = Number(val)
  if (isNaN(n)) return '--'
  return n.toFixed(1)
}

/** 格式化温度 */
export const fmtTemp = (val) => {
  const f = fmt1(val)
  return f === '--' ? '--' : `${f}°C`
}

/** 格式化湿度 */
export const fmtHumi = (val) => {
  const f = fmt1(val)
  return f === '--' ? '--' : `${f}%`
}

/** 格式化光照（整数即可，lux 通常不用小数） */
export const fmtLux = (val) => {
  if (val === null || val === undefined || val === '') return '--'
  const n = Number(val)
  if (isNaN(n)) return '--'
  return `${Math.round(n)} lux`
}
