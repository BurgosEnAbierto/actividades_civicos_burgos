/**
 * uiRenderer.js - Renderizado de elementos HTML
 */

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
    fechaInput.value = todayDate;
  }
}

/**
 * Renderiza la lista de actividades
 * @param {Array} activities - Array de actividades a renderizar
 * @param {Object} civicosMap - Mapeo de ID -> datos civico
 */
export function renderActivities(activities, civicosMap) {
  const container = document.getElementById('activities');
  if (!container) return;

  container.innerHTML = '';

  if (activities.length === 0) {
    container.innerHTML =
      '<div class="no-activities">No hay actividades que coincidan con los filtros</div>';
    return;
  }

  activities.forEach(act => {
    const activityElement = createActivityElement(act, civicosMap);
    container.appendChild(activityElement);
  });
}

/**
 * Crea un elemento DOM para una actividad
 * @param {Object} act - Actividad
 * @param {Object} civicosMap - Mapeo de ID -> datos civico
 * @returns {HTMLElement}
 */
function createActivityElement(act, civicosMap) {
  const div = document.createElement('div');
  div.className = 'activity';

  const civicName = civicosMap[act.civico]?.nombre || act.civico;
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
  detail.innerHTML = createActivityDetailHTML(act);

  div.appendChild(summary);
  div.appendChild(detail);

  div.addEventListener('click', () => {
    div.classList.toggle('expanded');
    detail.classList.toggle('hidden');
  });

  return div;
}

/**
 * Crea el HTML del detalle de una actividad
 * @param {Object} act - Actividad
 * @returns {string} HTML del detalle
 */
function createActivityDetailHTML(act) {
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

  return items
    .map(
      item => `
      <div class="activity-detail-item">
        <div class="activity-detail-label">${escapeHtml(item.label)}</div>
        <div class="activity-detail-value">${escapeHtml(item.value)}</div>
      </div>
    `
    )
    .join('');
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
