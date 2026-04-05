/**
 * dataLoader.js - Módulo para cargar datos desde archivos JSON
 */

/**
 * Obtiene los meses disponibles en /data/
 * Prioridad: mes actual, mes siguiente (si existe), mes anterior (si existe)
 * @returns {Promise<string[]>} Array de meses en formato YYYYMM ordenados descendentemente
 */
export async function getAvailableMonths() {
  const months = [];
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonthNum = currentDate.getMonth() + 1;

  // Calcular los meses a buscar: anterior, actual, siguiente
  const monthsToCheck = [
    // Mes anterior
    {
      date: new Date(currentYear, currentMonthNum - 2, 1),
      order: 3
    },
    // Mes actual
    {
      date: new Date(currentYear, currentMonthNum - 1, 1),
      order: 1
    },
    // Mes siguiente
    {
      date: new Date(currentYear, currentMonthNum, 1),
      order: 2
    }
  ];

  const monthsData = [];

  // Buscar datos para cada mes
  for (const entry of monthsToCheck) {
    const year = entry.date.getFullYear();
    const month = String(entry.date.getMonth() + 1).padStart(2, '0');
    const monthStr = `${year}${month}`;

    try {
      const response = await fetch(`data/${monthStr}/actividades.json`);
      if (response.ok) {
        monthsData.push({
          monthStr,
          order: entry.order
        });
      }
    } catch (err) {
      // Silenciosamente ignorar errores de fetch
    }
  }

  // Ordenar por prioridad (actual, siguiente, anterior) y luego descendentemente
  monthsData.sort((a, b) => {
    if (a.order !== b.order) {
      return a.order - b.order;
    }
    return b.monthStr.localeCompare(a.monthStr);
  });

  return monthsData.map(entry => entry.monthStr);
}

/**
 * Carga los datos de civicos desde civicos.json
 * @returns {Promise<Object>} Objeto con id -> civico data
 */
export async function loadCivicos() {
  try {
    const res = await fetch('data/civicos.json');
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
    const res = await fetch(`data/${monthStr}/actividades.json`);
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
 * Carga los links de PDFs de un mes específico
 * @param {string} monthStr - Mes en formato YYYYMM
 * @returns {Promise<Object>} Objeto con civico_id -> URL del PDF
 */
export async function loadLinksForMonth(monthStr) {
  try {
    const res = await fetch(`data/${monthStr}/links.json`);
    if (!res.ok) {
      return {};
    }
    const data = await res.json();
    // Convertir array de links a objeto civico_id -> url
    const linksMap = {};
    if (data.links && Array.isArray(data.links)) {
      data.links.forEach(link => {
        linksMap[link.civico_id] = link.url;
      });
    }
    return linksMap;
  } catch (err) {
    console.error(`Error cargando links del mes ${monthStr}:`, err);
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
