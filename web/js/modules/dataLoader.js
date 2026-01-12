/**
 * dataLoader.js - Módulo para cargar datos desde archivos JSON
 */

/**
 * Obtiene los meses disponibles en /data/
 * @returns {Promise<string[]>} Array de meses en formato YYYYMM ordenados descendentemente
 */
export async function getAvailableMonths() {
  const months = [];
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonthNum = currentDate.getMonth() + 1;

  // Buscar meses de los últimos 12 meses
  for (let i = 0; i < 12; i++) {
    let d = new Date(currentYear, currentMonthNum - 1 - i, 1);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const monthStr = `${year}${month}`;

    const response = await fetch(`../data/${monthStr}/actividades.json`)
      .then(res => (res.ok ? res.json().then(() => monthStr) : null))
      .catch(() => null);

    if (response) {
      months.push(monthStr);
    }
  }

  return months.sort().reverse();
}

/**
 * Carga los datos de civicos desde civicos.json
 * @returns {Promise<Object>} Objeto con id -> civico data
 */
export async function loadCivicos() {
  try {
    const res = await fetch('../data/civicos.json');
    return await res.json();
  } catch (err) {
    console.error('Error cargando civicos.json:', err);
    return {};
  }
}

/**
 * Carga las actividades de un mes específico
 * @param {string} monthStr - Mes en formato YYYYMM
 * @returns {Promise<Object>} Objeto con civico_id -> array de actividades
 */
export async function loadActivitiesForMonth(monthStr) {
  try {
    const res = await fetch(`../data/${monthStr}/actividades.json`);
    if (!res.ok) {
      throw new Error(`No encontrado: ${monthStr}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`Error cargando actividades del mes ${monthStr}:`, err);
    return {};
  }
}

/**
 * Normaliza los datos cargados a formato de lista plana con id de civico
 * @param {Object} data - Objeto con civico_id -> array de actividades
 * @returns {Array} Array de actividades con campo 'civico' añadido
 */
export function normalizeActivities(data) {
  const activities = [];
  for (const civico in data) {
    data[civico].forEach(act => {
      activities.push({ ...act, civico });
    });
  }
  return activities;
}
