/**
 * dateUtils.js - Utilidades para manejo de fechas
 */

/**
 * Parsea una fecha en formato DD/MM/YYYY a Date
 * @param {string} str - Fecha en formato DD/MM/YYYY
 * @returns {Date} Objeto Date
 */
export function parseDate(str) {
  const [d, m, y] = str.split('/').map(Number);
  return new Date(y, m - 1, d);
}

/**
 * Formatea un mes YYYYMM a texto legible
 * @param {string} monthStr - Mes en formato YYYYMM
 * @returns {string} Formato "Enero 2025"
 */
export function formatMonth(monthStr) {
  const year = parseInt(monthStr.substring(0, 4));
  const month = parseInt(monthStr.substring(4, 6));
  const monthNames = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  return `${monthNames[month - 1]} ${year}`;
}

/**
 * Verifica si una actividad está dentro de un rango de fechas
 * @param {Object} activity - Actividad con fecha y fecha_fin
 * @param {Date} selectedDate - Fecha a comprobar
 * @returns {boolean} true si la actividad se solapea con selectedDate
 */
export function isActivityInDateRange(activity, selectedDate) {
  const inicio = parseDate(activity.fecha);
  inicio.setHours(0, 0, 0, 0);

  const fin = activity.fecha_fin ? parseDate(activity.fecha_fin) : inicio;
  fin.setHours(0, 0, 0, 0);

  selectedDate.setHours(0, 0, 0, 0);

  return selectedDate >= inicio && selectedDate <= fin;
}
