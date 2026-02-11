# Web - Burgos Civicos

Frontend para visualizar la agenda de actividades de los centros cívicos de Burgos.

## 🚀 Inicio rápido

### Ver la web
```bash
npm run server
```
Abre http://localhost:8000/web/index.html

### Ejecutar tests
```bash
npm install
npm test
```

## 📁 Organización del código

```
web/js/
├── modules/              # Módulos funcionales
│   ├── app.js           # Orquestación principal (clase App)
│   ├── dataLoader.js    # Carga de datos (civicos, actividades, meses)
│   ├── dateUtils.js     # Utilidades de fechas
│   ├── filterEngine.js  # Lógica de filtrado
│   └── uiRenderer.js    # Renderizado de elementos HTML
│
└── __tests__/            # Tests unitarios
    ├── dateUtils.test.js (6 tests)
    └── filterEngine.test.js (9 tests)
```

## 🧩 Módulos

**`app.js`** - Orquestador principal
- Clase `App` que coordina todo el flujo
- Métodos: `init()`, `loadCivicos()`, `loadAvailableMonths()`, `applyFilters()`

**`dataLoader.js`** - Carga de datos desde JSON
- `getAvailableMonths()` - Detecta meses disponibles en `/docs/data/`
- `loadCivicos()` - Carga `/docs/data/civicos.json`
- `loadActivitiesForMonth(monthStr)` - Carga `/docs/data/YYYYMM/actividades.json`
- `normalizeActivities(data)` - Convierte estructura anidada a array plano

**`dateUtils.js`** - Utilidades de fechas
- `parseDate(str)` - Parsea `DD/MM/YYYY` a `Date`
- `formatMonth(monthStr)` - Convierte `YYYYMM` a formato legible
- `isActivityInDateRange(activity, date)` - Valida rangos de fechas

**`filterEngine.js`** - Lógica de filtrado
- `applyFilters(activities, filters)` - Aplica múltiples filtros simultáneamente
- `getUniqueCivicos(activities)` - Extrae civicos únicos y ordenados
- Lógica pura sin dependencias de UI

**`uiRenderer.js`** - Renderizado HTML
- `renderMonthSelector()` - Selector de meses
- `renderFilters()` - Campos de filtrado
- `renderActivities()` - Lista de actividades con detalles expandibles

## 🧪 Tests

15 tests unitarios distribuidos en 2 archivos:

**dateUtils.test.js** (6 tests)
- Parsing de fechas en formato DD/MM/YYYY
- Formateo de meses YYYYMM
- Validación de rangos de fechas (inicio, fin, interior)

**filterEngine.test.js** (9 tests)
- Filtrado individual por civico, fecha, público, inscripción
- Filtrado case-insensitive en público
- Combinación de múltiples filtros simultáneamente
- Extracción de civicos únicos

Ejecutar:
```bash
npm test              # Ejecutar todos
npm run test:watch    # Modo watch
npm run test:coverage # Ver cobertura
```

## 📦 Dependencias

**Runtime:** Ninguna (JS vanilla)

**Dev:**
- jest - Framework de testing
- @babel/preset-env - Transpilación ES6
- babel-jest - Integración con Jest
- jest-environment-jsdom - Entorno DOM para tests

## 🔍 Flujo de inicialización

1. HTML carga `<script type="module" src="js/modules/app.js">`
2. `app.js` importa módulos
3. `App.init()` ejecuta:
   - Carga civicos y meses en paralelo
   - Carga actividades del mes más reciente
   - Renderiza interfaz
   - Conecta event listeners

## 💡 Arquitectura

Cada módulo tiene una responsabilidad única:
- **app.js** - Orquestación y estado
- **dataLoader.js** - Entrada de datos (fetch)
- **dateUtils.js** - Transformación de fechas (puro)
- **filterEngine.js** - Lógica de negocio (puro)
- **uiRenderer.js** - Salida de datos (DOM)

Los módulos son independientes y reutilizables. Las funciones de lógica pura (`dateUtils`, `filterEngine`) son fáciles de testear sin mocking.

## 🔧 Scripts disponibles

```bash
npm test              # Ejecutar tests
npm run test:watch    # Tests en modo watch
npm run test:coverage # Cobertura de tests
npm run server        # Servidor HTTP puerto 8000
```

## 📝 Estructura del HTML

- `index.html` - 85 líneas, estructura limpia
- Estilos CSS inline (pueden extraerse)
- Una sola línea de JS: carga modular
- Sin dependencias externas

