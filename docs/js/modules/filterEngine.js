/**
 * filterEngine.js - Lógica de filtrado de actividades
 */

import { isActivityInDateRange } from './dateUtils.js';

/**
 * Aplica filtros a un array de actividades
 * @param {Array} activities - Array de actividades
 * @param {Object} filters - Objeto con filtros
 * @param {string} filters.civico - ID del civico (vacío = todos)
 * @param {string} filters.fecha - Fecha en formato YYYY-MM-DD
 * @param {string} filters.publico - Texto a buscar en público
 * @param {string} filters.inscripcion - 'true'|'false'|'' (vacío = todos)
 * @returns {Array} Actividades filtradas
 */
export function applyFilters(activities, filters) {
  let filtered = activities.slice();

  // Filtro por civico
  if (filters.civico) {
    filtered = filtered.filter(a => a.civico === filters.civico);
  }

  // Filtro por fecha
  if (filters.fecha) {
    const [y, m, d] = filters.fecha.split('-').map(Number);
    const selectedDate = new Date(y, m - 1, d);
    filtered = filtered.filter(a => isActivityInDateRange(a, selectedDate));
  }

  // Filtro por público
  if (filters.publico) {
    const publicoLower = filters.publico.toLowerCase();
    filtered = filtered.filter(a =>
      a.publico && a.publico.toLowerCase().includes(publicoLower)
    );
  }

  // Filtro por inscripción
  if (filters.inscripcion) {
    const val = filters.inscripcion === 'true';
    filtered = filtered.filter(a => a.requiere_inscripcion === val);
  }

  return filtered;
}

/**
 * Obtiene los civicos únicos de un array de actividades
 * @param {Array} activities - Array de actividades
 * @returns {Array<string>} Array ordenado de IDs de civicos únicos
 */
export function getUniqueCivicos(activities) {
  return [...new Set(activities.map(a => a.civico))].sort();
}
