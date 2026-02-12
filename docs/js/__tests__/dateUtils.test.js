/**
 * dateUtils.test.js - Tests para utilidades de fechas
 */

import { parseDate, formatMonth, isActivityInDateRange } from '../modules/dateUtils.js';

describe('dateUtils', () => {
  describe('parseDate', () => {
    test('debería parsear una fecha DD/MM/YYYY correctamente', () => {
      const result = parseDate('15/03/2025');
      expect(result).toEqual(new Date(2025, 2, 15));
    });

    test('debería manejar fechas con día/mes de un dígito', () => {
      const result = parseDate('05/01/2025');
      expect(result).toEqual(new Date(2025, 0, 5));
    });

    test('debería manejar la fecha máxima del mes', () => {
      const result = parseDate('31/12/2025');
      expect(result).toEqual(new Date(2025, 11, 31));
    });
  });

  describe('formatMonth', () => {
    test('debería formatear 202501 a "Enero 2025"', () => {
      expect(formatMonth('202501')).toBe('Enero 2025');
    });

    test('debería formatear 202512 a "Diciembre 2025"', () => {
      expect(formatMonth('202512')).toBe('Diciembre 2025');
    });

    test('debería formatear 202606 a "Junio 2026"', () => {
      expect(formatMonth('202606')).toBe('Junio 2026');
    });
  });

  describe('isActivityInDateRange', () => {
    const activity = {
      fecha: '10/03/2025',
      fecha_fin: '15/03/2025'
    };

    test('debería retornar true si la fecha está dentro del rango', () => {
      const selectedDate = new Date(2025, 2, 12);
      expect(isActivityInDateRange(activity, selectedDate)).toBe(true);
    });

    test('debería retornar true si la fecha es el inicio del rango', () => {
      const selectedDate = new Date(2025, 2, 10);
      expect(isActivityInDateRange(activity, selectedDate)).toBe(true);
    });

    test('debería retornar true si la fecha es el fin del rango', () => {
      const selectedDate = new Date(2025, 2, 15);
      expect(isActivityInDateRange(activity, selectedDate)).toBe(true);
    });

    test('debería retornar false si la fecha está fuera del rango', () => {
      const selectedDate = new Date(2025, 2, 20);
      expect(isActivityInDateRange(activity, selectedDate)).toBe(false);
    });

    test('debería manejar actividades sin fecha_fin', () => {
      const singleDayActivity = {
        fecha: '10/03/2025',
        fecha_fin: null
      };
      const selectedDate = new Date(2025, 2, 10);
      expect(isActivityInDateRange(singleDayActivity, selectedDate)).toBe(true);
    });
  });
});
