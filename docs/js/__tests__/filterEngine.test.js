/**
 * filterEngine.test.js - Tests para el motor de filtrado
 */

import { applyFilters, getUniqueCivicos } from '../modules/filterEngine.js';

describe('filterEngine', () => {
  const mockActivities = [
    {
      nombre: 'Yoga',
      fecha: '10/03/2025',
      fecha_fin: null,
      civico: 'gamonal_norte',
      publico: 'adultos',
      requiere_inscripcion: true
    },
    {
      nombre: 'Taller infantil',
      fecha: '12/03/2025',
      fecha_fin: null,
      civico: 'rio_vena',
      publico: 'niños de 5 a 10 años',
      requiere_inscripcion: false
    },
    {
      nombre: 'Exposición',
      fecha: '01/03/2025',
      fecha_fin: '31/03/2025',
      civico: 'capiscol',
      publico: 'público general',
      requiere_inscripcion: false
    }
  ];

  describe('applyFilters', () => {
    test('debería retornar todas las actividades sin filtros', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '',
        publico: '',
        inscripcion: ''
      });
      expect(result).toHaveLength(3);
    });

    test('debería filtrar por civico', () => {
      const result = applyFilters(mockActivities, {
        civico: 'gamonal_norte',
        fecha: '',
        publico: '',
        inscripcion: ''
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Yoga');
    });

    test('debería filtrar por fecha exacta', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '2025-03-12',
        publico: '',
        inscripcion: ''
      });
      expect(result).toHaveLength(2);
      expect(result.map(a => a.nombre)).toContain('Taller infantil');
      expect(result.map(a => a.nombre)).toContain('Exposición');
    });

    test('debería filtrar por fecha dentro de rango', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '2025-03-15',
        publico: '',
        inscripcion: ''
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Exposición');
    });

    test('debería filtrar por público (búsqueda text)', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '',
        publico: 'niños',
        inscripcion: ''
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Taller infantil');
    });

    test('debería filtrar por público case-insensitive', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '',
        publico: 'ADULTOS',
        inscripcion: ''
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Yoga');
    });

    test('debería filtrar por inscripción requerida', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '',
        publico: '',
        inscripcion: 'true'
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Yoga');
    });

    test('debería filtrar por inscripción no requerida', () => {
      const result = applyFilters(mockActivities, {
        civico: '',
        fecha: '',
        publico: '',
        inscripcion: 'false'
      });
      expect(result).toHaveLength(2);
    });

    test('debería combinar múltiples filtros', () => {
      const result = applyFilters(mockActivities, {
        civico: 'rio_vena',
        fecha: '2025-03-12',
        publico: 'niños',
        inscripcion: 'false'
      });
      expect(result).toHaveLength(1);
      expect(result[0].nombre).toBe('Taller infantil');
    });
  });

  describe('getUniqueCivicos', () => {
    test('debería retornar civicos únicos y ordenados', () => {
      const result = getUniqueCivicos(mockActivities);
      expect(result).toEqual(['capiscol', 'gamonal_norte', 'rio_vena']);
    });

    test('debería manejar array vacío', () => {
      const result = getUniqueCivicos([]);
      expect(result).toEqual([]);
    });

    test('debería manejar actividades con mismo civico', () => {
      const activities = [
        { civico: 'gamonal_norte' },
        { civico: 'gamonal_norte' }
      ];
      const result = getUniqueCivicos(activities);
      expect(result).toEqual(['gamonal_norte']);
    });
  });
});
