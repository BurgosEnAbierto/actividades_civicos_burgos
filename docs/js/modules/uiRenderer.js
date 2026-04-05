/**
 * uiRenderer.js - Renderizado de elementos HTML
 */

import * as feedbackHandler from './feedbackHandler.js';
import * as shareHandler from './shareHandler.js';

/**
 * Renderiza el selector de meses
 * @param {Array<string>} months - Array de meses en YYYYMM
 * @param {string} currentMonth - Mes seleccionado actualmente
 * @param {Function} formatMonth - Función para formatear meses
 */
export function renderMonthSelector(months, currentMonth, formatMonth) {
  const select = document.getElementById('monthSelect');
  if (!select) return;

  select.innerHTML = '';
  months.forEach(monthStr => {
    const opt = document.createElement('option');
    opt.value = monthStr;
    opt.textContent = formatMonth(monthStr);
    if (monthStr === currentMonth) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });
}

/**
 * Renderiza los filtros con los civicos disponibles
 * @param {Array<string>} civicos - Array de IDs de civicos
 * @param {Object} civicosMap - Mapeo de ID -> datos civico
 * @param {string} todayDate - Fecha de hoy en formato YYYY-MM-DD
 */
export function renderFilters(civicos, civicosMap, todayDate) {
  const selectCentro = document.getElementById('filterCentro');
  if (!selectCentro) return;

  const firstOption = selectCentro.querySelector('option[value=""]');
  selectCentro.innerHTML = '';
  selectCentro.appendChild(firstOption);

  civicos.forEach(civico => {
    const opt = document.createElement('option');
    opt.value = civico;
    const civicName = civicosMap[civico]?.nombre || civico;
    opt.textContent = civicName;
    selectCentro.appendChild(opt);
  });

  const fechaInput = document.getElementById('filterFecha');
  if (fechaInput) {
    fechaInput.value = '';
  }
}

/**
 * Renderiza la lista de actividades
 * @param {Array} activities - Array de actividades a renderizar
 * @param {Object} civicosMap - Mapeo de ID -> datos civico
 * @param {Object} linksMap - Mapeo de civico_id -> URL del PDF
 * @param {string} currentMonth - Mes en formato YYYYMM
 */
export function renderActivities(activities, civicosMap, linksMap = {}, currentMonth = '') {
  const container = document.getElementById('activities');
  if (!container) return;

  container.innerHTML = '';

  if (activities.length === 0) {
    container.innerHTML =
      '<div class="no-activities">No hay actividades que coincidan con los filtros</div>';
    return;
  }

  activities.forEach((act, index) => {
    const activityElement = createActivityElement(act, civicosMap, linksMap, currentMonth, index);
    container.appendChild(activityElement);
  });

  // Agregar event listeners a los botones de compartir
  setupShareButtonListeners(container);
}

/**
 * Configura los event listeners para los botones de compartir
 * @param {HTMLElement} container - Contenedor que tiene los botones
 */
function setupShareButtonListeners(container) {
  const shareButtons = container.querySelectorAll('.share-button');
  shareButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      const platform = button.dataset.platform;
      const url = button.dataset.url;
      const title = button.dataset.title;
      const text = button.dataset.text;
      
      await shareHandler.handleShareClick(platform, url, title, text);
    });
  });
}

/**
 * Crea un elemento DOM para una actividad
 * @param {Object} act - Actividad
 * @param {Object} civicosMap - Mapeo de ID -> datos civico
 * @param {Object} linksMap - Mapeo de civico_id -> URL del PDF
 * @param {string} currentMonth - Mes en formato YYYYMM
 * @param {number} index - Índice de la actividad en la lista
 * @returns {HTMLElement}
 */
function createActivityElement(act, civicosMap, linksMap = {}, currentMonth = '', index = 0) {
  const div = document.createElement('div');
  div.className = 'activity';
  const activityId = shareHandler.generateActivityId(act, index);
  div.id = activityId;

  const civicName = civicosMap[act.civico]?.nombre || act.civico;
  const civicPhone = civicosMap[act.civico]?.telefono;
  const pdfUrl = linksMap[act.civico];
  const inscriptionText = act.requiere_inscripcion
    ? 'Requiere inscripción'
    : 'Sin inscripción';

  const summary = document.createElement('div');
  summary.className = 'activity-summary';
  summary.innerHTML = `
    <div class="activity-summary-title">
      ${escapeHtml(act.nombre)}
      <span class="expand-icon">▼</span>
    </div>
    <div class="activity-summary-date">${act.fecha}</div>
    <div class="activity-summary-centro">${escapeHtml(civicName)}</div>
    <div class="activity-summary-inscription">${inscriptionText}</div>
  `;

  const detail = document.createElement('div');
  detail.className = 'activity-detail hidden';
  detail.innerHTML = createActivityDetailHTML(act, pdfUrl, civicPhone, civicName, currentMonth, index);

  div.appendChild(summary);
  div.appendChild(detail);

  summary.addEventListener('click', (e) => {
    // Solo cerrar si el click es en el summary, no en los enlaces del detail
    div.classList.toggle('expanded');
    detail.classList.toggle('hidden');
  });

  return div;
}

/**
 * Crea el HTML del detalle de una actividad
 * @param {Object} act - Actividad
 * @param {string} pdfUrl - URL del PDF de la actividad
 * @param {string} civicPhone - Teléfono del cívico
 * @param {string} civicName - Nombre del cívico
 * @param {string} currentMonth - Mes en formato YYYYMM
 * @param {number} index - Índice de la actividad en la lista
 * @returns {string} HTML del detalle
 */
function createActivityDetailHTML(act, pdfUrl, civicPhone, civicName, currentMonth = '', index = 0) {
  const items = [];

  if (act.descripcion) {
    items.push({ label: 'Descripción', value: act.descripcion });
  }

  if (act.hora || act.hora_fin) {
    const horaStr = act.hora ? `${act.hora}` : '';
    const horaFinStr = act.hora_fin ? ` - ${act.hora_fin}` : '';
    items.push({
      label: 'Hora',
      value: `${horaStr}${horaFinStr}`
    });
  }

  if (act.fecha_fin && act.fecha_fin !== act.fecha) {
    items.push({
      label: 'Hasta',
      value: act.fecha_fin
    });
  }

  items.push({
    label: 'Público',
    value: act.publico
  });

  if (act.lugar) {
    items.push({
      label: 'Lugar',
      value: act.lugar
    });
  }

  if (act.edad_minima || act.edad_maxima) {
    const edadMin = act.edad_minima ? `${act.edad_minima}` : '';
    const edadMax = act.edad_maxima ? `${act.edad_maxima}` : '';
    if (edadMin && edadMax) {
      items.push({
        label: 'Edad',
        value: `${edadMin} - ${edadMax} años`
      });
    } else if (edadMin) {
      items.push({
        label: 'Edad mínima',
        value: `${edadMin} años`
      });
    } else if (edadMax) {
      items.push({
        label: 'Edad máxima',
        value: `${edadMax} años`
      });
    }
  }

  if (act.precio !== null && act.precio !== undefined) {
    items.push({
      label: 'Precio',
      value: act.precio > 0 ? `${act.precio} €` : 'Gratuita'
    });
  } else {
    items.push({
      label: 'Precio',
      value: 'Gratuita'
    });
  }

  let detailHTML = items
    .map(
      item => `
      <div class="activity-detail-item">
        <div class="activity-detail-label">${escapeHtml(item.label)}</div>
        <div class="activity-detail-value">${escapeHtml(item.value)}</div>
      </div>
    `
    )
    .join('');

  // Agregar sección de acciones (enlaces)
  detailHTML += '<div class="activity-actions">';

  if (pdfUrl) {
    detailHTML += `
      <a href="${escapeHtml(pdfUrl)}" target="_blank" rel="noopener noreferrer" class="action-link pdf-link">
        📄 Ver actividad en el PDF original
      </a>
    `;
  }

  if (civicPhone) {
    detailHTML += `
      <a href="tel:${escapeHtml(civicPhone)}" class="action-link phone-link" title="Llamar a ${escapeHtml(civicName)}">
        ☎️ Contactar con el Cívico
      </a>
      <div class="action-link phone-number" title="Copiar número de teléfono">
        📋 ${escapeHtml(civicPhone)}
      </div>
    `;
  }

  // Agregar botón "Reportar problema"
  const mailtoUrl = feedbackHandler.generateActivityReportMailto(act, civicName, currentMonth);
  detailHTML += `
    <a href="${escapeHtml(mailtoUrl)}" class="action-link report-link" title="Reportar un problema en esta actividad">
      ⚠️ Reportar problema
    </a>
  `;

  // Agregar sección de compartir
  const shareUrl = shareHandler.generateActivityShareUrl(act, currentMonth, index);
  const shareTitle = `${act.nombre} - Centros Cívicos de Burgos`;
  const shareText = `Mira esta actividad en la agenda de actividades de Centros Cívicos de Burgos:`;
  
  detailHTML += '<div class="activity-share-buttons">';
  detailHTML += `
    <button class="share-button share-whatsapp" title="Compartir por WhatsApp" data-platform="whatsapp" data-url="${escapeHtml(shareUrl)}" data-title="${escapeHtml(shareTitle)}" data-text="${escapeHtml(shareText)}">
      💬
    </button>
    <button class="share-button share-twitter" title="Compartir en Twitter" data-platform="twitter" data-url="${escapeHtml(shareUrl)}" data-title="${escapeHtml(shareTitle)}" data-text="${escapeHtml(shareText)}">
      𝕏
    </button>
    <button class="share-button share-facebook" title="Compartir en Facebook" data-platform="facebook" data-url="${escapeHtml(shareUrl)}" data-title="${escapeHtml(shareTitle)}" data-text="${escapeHtml(shareText)}">
      📘
    </button>
    <button class="share-button share-email" title="Compartir por email" data-platform="email" data-url="${escapeHtml(shareUrl)}" data-title="${escapeHtml(shareTitle)}" data-text="${escapeHtml(shareText)}">
      ✉️
    </button>
    <button class="share-button share-copy" title="Copiar enlace" data-platform="copy" data-url="${escapeHtml(shareUrl)}" data-title="${escapeHtml(shareTitle)}" data-text="${escapeHtml(shareText)}">
      📋
    </button>
  `;
  detailHTML += '</div>';

  detailHTML += '</div>';

  return detailHTML;
}

/**
 * Escapa caracteres HTML para prevenir XSS
 * @param {string} text - Texto a escapar
 * @returns {string} Texto escapado
 */
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
