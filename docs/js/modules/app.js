/**
 * app.js - Módulo principal de orquestación
 */

import * as dataLoader from './dataLoader.js';
import * as dateUtils from './dateUtils.js';
import * as filterEngine from './filterEngine.js';
import * as uiRenderer from './uiRenderer.js';
import * as versionLoader from './versionLoader.js';
import * as shareHandler from './shareHandler.js';

class App {
  constructor() {
    this.allActivities = [];
    this.civicosMap = {};
    this.linksMap = {};
    this.availableMonths = [];
    this.currentMonth = null;
    this.currentFilters = {
      civico: '',
      fecha: '',
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
   * Obtiene los parámetros de URL (month, activity)
   * @returns {Object} {month, activity}
   */
  getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      month: params.get('month'),
      activity: params.get('activity')
    };
  }

  /**
   * Inicializa la aplicación
   */
  async init() {
    try {
      // Cargar civicos, meses disponibles y versión en paralelo
      await Promise.all([
        this.loadCivicos(),
        this.loadAvailableMonths(),
        this.loadAndDisplayVersion()
      ]);

      if (this.availableMonths.length === 0) {
        this.showNoDataMessage();
        return;
      }

      // Obtener parámetros de URL
      const urlParams = this.getUrlParams();
      
      // Si hay un mes en la URL, usarlo; si no, usar el más reciente
      if (urlParams.month && this.availableMonths.includes(urlParams.month)) {
        this.currentMonth = urlParams.month;
      } else {
        this.currentMonth = this.availableMonths[0];
      }

      // Cargar datos del mes actual
      await this.loadCurrentMonth();

      // Inicializar interfaz
      this.setupUI();
      this.applyFilters();

      // Si hay una actividad en la URL, expandirla después de renderizar
      if (urlParams.activity) {
        this.expandActivityFromUrl(urlParams.activity);
      }
    } catch (err) {
      console.error('Error inicializando aplicación:', err);
      this.showErrorMessage('Error al cargar la aplicación');
    }
  }

  /**
   * Expande una actividad específica basada en su ID desde la URL
   * @param {string} activityId - ID de la actividad
   */
  expandActivityFromUrl(activityId) {
    // Esperar un pequeño delay para asegurar que el DOM esté actualizado
    setTimeout(() => {
      const element = document.getElementById(activityId);
      if (element) {
        // Hacer scroll al elemento
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Expandir la actividad
        const summary = element.querySelector('.activity-summary');
        const detail = element.querySelector('.activity-detail');
        if (summary && detail) {
          element.classList.add('expanded');
          detail.classList.remove('hidden');
        }
      }
    }, 100);
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
   * Carga y muestra la versión del proyecto
   */
  async loadAndDisplayVersion() {
    const version = await versionLoader.loadVersion();
    versionLoader.updateFooterVersion(version);
  }

  /**
   * Carga las actividades del mes actual
   */
  async loadCurrentMonth() {
    const data = await dataLoader.loadActivitiesForMonth(this.currentMonth);
    this.allActivities = dataLoader.normalizeActivities(data);
    
    // Cargar también los links de PDFs del mes
    this.linksMap = await dataLoader.loadLinksForMonth(this.currentMonth);
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

    // Configurar botones de compartir en el header
    this.setupHeaderShareButtons();
  }

  /**
   * Configura los botones de compartir en el header
   */
  setupHeaderShareButtons() {
    const shareUrl = shareHandler.generateWebShareUrl();
    const shareTitle = 'Agenda de actividades de Centros Cívicos de Burgos';
    const shareText = 'Consulta la agenda de actividades de los Centros Cívicos de Burgos';

    const shareButtons = {
      'shareWhatsapp': 'whatsapp',
      'shareTwitter': 'twitter',
      'shareFacebook': 'facebook',
      'shareEmail': 'email',
      'shareCopy': 'copy'
    };

    for (const [buttonId, platform] of Object.entries(shareButtons)) {
      const button = document.getElementById(buttonId);
      if (button) {
        button.addEventListener('click', async (e) => {
          e.preventDefault();
          await shareHandler.handleShareClick(platform, shareUrl, shareTitle, shareText);
        });
      }
    }
  }

  /**
   * Handler para cambio de mes
   */
  async onMonthChange(e) {
    this.currentMonth = e.target.value;
    if (!this.currentMonth) return;

    await this.loadCurrentMonth();

    // Reinicializar filtros (estado y DOM)
    this.currentFilters = {
      civico: '',
      fecha: '',
      publico: '',
      inscripcion: ''
    };

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
    uiRenderer.renderActivities(filtered, this.civicosMap, this.linksMap, this.currentMonth);
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
