/**
 * app.js - Módulo principal de orquestación
 */

import * as dataLoader from './dataLoader.js';
import * as dateUtils from './dateUtils.js';
import * as filterEngine from './filterEngine.js';
import * as uiRenderer from './uiRenderer.js';

class App {
  constructor() {
    this.allActivities = [];
    this.civicosMap = {};
    this.availableMonths = [];
    this.currentMonth = null;
    this.currentFilters = {
      civico: '',
      fecha: this.getTodayDateString(),
      publico: '',
      inscripcion: ''
    };
  }

  /**
   * Obtiene la fecha de hoy en formato YYYY-MM-DD
   */
  getTodayDateString() {
    const today = new Date();
    return today.toISOString().split('T')[0];
  }

  /**
   * Inicializa la aplicación
   */
  async init() {
    try {
      // Cargar civicos y meses disponibles en paralelo
      await Promise.all([
        this.loadCivicos(),
        this.loadAvailableMonths()
      ]);

      if (this.availableMonths.length === 0) {
        this.showNoDataMessage();
        return;
      }

      // Cargar mes más reciente por defecto
      this.currentMonth = this.availableMonths[0];

      // Cargar datos del mes actual
      await this.loadCurrentMonth();

      // Inicializar interfaz
      this.setupUI();
      this.applyFilters();
    } catch (err) {
      console.error('Error inicializando aplicación:', err);
      this.showErrorMessage('Error al cargar la aplicación');
    }
  }

  /**
   * Carga los datos de civicos
   */
  async loadCivicos() {
    this.civicosMap = await dataLoader.loadCivicos();
  }

  /**
   * Carga los meses disponibles
   */
  async loadAvailableMonths() {
    this.availableMonths = await dataLoader.getAvailableMonths();
  }

  /**
   * Carga las actividades del mes actual
   */
  async loadCurrentMonth() {
    const data = await dataLoader.loadActivitiesForMonth(this.currentMonth);
    this.allActivities = dataLoader.normalizeActivities(data);
  }

  /**
   * Configura los event listeners de la UI
   */
  setupUI() {
    // Renderizar selector de meses
    uiRenderer.renderMonthSelector(
      this.availableMonths,
      this.currentMonth,
      dateUtils.formatMonth
    );

    // Renderizar filtros
    const civicos = filterEngine.getUniqueCivicos(this.allActivities);
    uiRenderer.renderFilters(
      civicos,
      this.civicosMap,
      this.getTodayDateString()
    );

    // Event listeners
    const monthSelect = document.getElementById('monthSelect');
    const filterCentro = document.getElementById('filterCentro');
    const filterFecha = document.getElementById('filterFecha');
    const filterPublico = document.getElementById('filterPublico');
    const filterInscripcion = document.getElementById('filterInscripcion');

    if (monthSelect) {
      monthSelect.addEventListener('change', e => this.onMonthChange(e));
    }
    if (filterCentro) {
      filterCentro.addEventListener('change', e => this.onFilterChange(e));
    }
    if (filterFecha) {
      filterFecha.addEventListener('change', e => this.onFilterChange(e));
    }
    if (filterPublico) {
      filterPublico.addEventListener('change', e => this.onFilterChange(e));
    }
    if (filterInscripcion) {
      filterInscripcion.addEventListener('change', e => this.onFilterChange(e));
    }
  }

  /**
   * Handler para cambio de mes
   */
  async onMonthChange(e) {
    this.currentMonth = e.target.value;
    if (!this.currentMonth) return;

    await this.loadCurrentMonth();

    // Reinicializar filtros
    const civicos = filterEngine.getUniqueCivicos(this.allActivities);
    uiRenderer.renderFilters(
      civicos,
      this.civicosMap,
      this.getTodayDateString()
    );

    this.applyFilters();
  }

  /**
   * Handler para cambio de filtro
   */
  onFilterChange(e) {
    const id = e.target.id;
    const value = e.target.value;

    switch (id) {
      case 'filterCentro':
        this.currentFilters.civico = value;
        break;
      case 'filterFecha':
        this.currentFilters.fecha = value;
        break;
      case 'filterPublico':
        this.currentFilters.publico = value;
        break;
      case 'filterInscripcion':
        this.currentFilters.inscripcion = value;
        break;
    }

    this.applyFilters();
  }

  /**
   * Aplica los filtros actuales y renderiza
   */
  applyFilters() {
    const filtered = filterEngine.applyFilters(
      this.allActivities,
      this.currentFilters
    );
    uiRenderer.renderActivities(filtered, this.civicosMap);
  }

  /**
   * Muestra mensaje de error
   */
  showErrorMessage(msg) {
    const container = document.getElementById('activities');
    if (container) {
      container.innerHTML = `<div class="no-activities">Error: ${msg}</div>`;
    }
  }

  /**
   * Muestra mensaje cuando no hay datos
   */
  showNoDataMessage() {
    const container = document.getElementById('activities');
    if (container) {
      container.innerHTML =
        '<div class="no-activities">No hay datos de actividades disponibles</div>';
    }
  }
}

// Inicializar la aplicación cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
  });
} else {
  const app = new App();
  app.init();
}

export default App;
