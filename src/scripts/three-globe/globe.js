import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import * as THREE from 'three';
import ThreeGlobe from 'three-globe';
import countriesData from './countries.js';
import config from '../../config.json';

export const { globeViewWidth: renderWidth, globeViewHeight: renderHeight } = config;

const ARC_FLIGHT_MS = 2200;
const MAX_ARCS = 10000;
const MAX_VISITOR_PULSES = 32;
const MAX_POINTS = MAX_ARCS * 2 + 8;

// Bright cyan → soft white gradient for the glowing trail.
const ARC_COLOR_GRADIENT = ['rgba(56,189,248,0.95)', 'rgba(244,255,255,1)', 'rgba(56,189,248,0.95)'];
const SOURCE_POINT_COLOR = 'rgba(34, 211, 238, 0.98)';
const SERVER_POINT_COLOR = 'rgba(244, 114, 182, 0.9)';
const SERVER_RING_COLOR = (t) => `rgba(244, 114, 182, ${0.75 * (1 - t)})`;
const VISITOR_RING_COLOR = (t) => `rgba(34, 211, 238, ${1 - t})`;
const VISITOR_CORE_RING_COLOR = (t) => `rgba(255, 255, 255, ${0.9 * (1 - t)})`;
const DEFAULT_LAND_SHADE_MIN = 140;
const DEFAULT_LAND_SHADE_VARIATION = 115;
const CHINA_LAND_COLOR = 'rgb(92,92,92)';
const GLOBE_OCCLUSION_MATERIAL = new THREE.MeshPhongMaterial({
  color: 0xf8fafc,
  opacity: 0.42,
  transparent: true,
  depthTest: true,
  depthWrite: true,
  side: THREE.FrontSide,
  shininess: 8,
});

function isChinaFeature(feature) {
  const properties = feature?.properties;
  return properties?.ISO_A3 === 'CHN' || properties?.ADM0_A3 === 'CHN' || properties?.ADMIN === 'China';
}

function getLandHexColor(feature) {
  if (isChinaFeature(feature)) return CHINA_LAND_COLOR;

  const shade = Math.floor(Math.random() * DEFAULT_LAND_SHADE_VARIATION + DEFAULT_LAND_SHADE_MIN);
  return `rgb(${shade},${shade},${shade})`;
}

function formatSource(source) {
  if (!source) return '—';
  const place = [source.city, source.country].filter(Boolean).join(', ');
  return place || `${source.lat.toFixed(2)}, ${source.lng.toFixed(2)}`;
}

function formatServer(server) {
  if (!server) return '—';
  return `${server.label} (${server.code})`;
}

function formatVisitTime(ts) {
  if (!Number.isFinite(ts)) return '—';
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(ts));
}

export function initGlobe() {
  const arcs = [];
  const rings = [];
  const points = [];

  const Globe = new ThreeGlobe({ animateIn: false })
    .showAtmosphere(false)
    .hexPolygonsData(countriesData.features)
    .hexPolygonResolution(3)
    .hexPolygonMargin(0.1)
    .hexPolygonUseDots(true)
    .hexPolygonColor(getLandHexColor)
    .hexPolygonAltitude(0.001)
    .globeMaterial(GLOBE_OCCLUSION_MATERIAL)
    // Endpoint dots. The expanding rings are the animation; the dots keep the
    // source and server locations readable between ring waves.
    .pointsData(points)
    .pointLat((d) => d.lat)
    .pointLng((d) => d.lng)
    .pointAltitude((d) => d.altitude)
    .pointRadius((d) => d.radius)
    .pointColor((d) => d.color)
    .pointsMerge(false)
    .pointsTransitionDuration(250)
    // Arcs (visitor → server, glowing dashed flow).
    .arcsData(arcs)
    .arcStartLat((d) => d.startLat)
    .arcStartLng((d) => d.startLng)
    .arcEndLat((d) => d.endLat)
    .arcEndLng((d) => d.endLng)
    .arcColor((d) => d.color)
    .arcStroke((d) => d.stroke)
    .arcAltitudeAutoScale((d) => d.altitudeScale)
    .arcDashLength((d) => d.dashLength)
    .arcDashGap((d) => d.dashGap)
    .arcDashInitialGap((d) => d.dashInitialGap)
    .arcDashAnimateTime((d) => d.animateTime)
    .arcsTransitionDuration(0)
    // Rings (pulsing endpoints).
    .ringsData(rings)
    .ringLat((d) => d.lat)
    .ringLng((d) => d.lng)
    .ringColor((d) => d.color)
    .ringMaxRadius((d) => d.maxRadius)
    .ringPropagationSpeed((d) => d.speed)
    .ringRepeatPeriod((d) => d.repeat);

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(renderWidth, renderHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  const globeRoot = document.getElementById('globe-point-cloud');
  const globeContainer = document.getElementById('globe-container');
  globeRoot.appendChild(renderer.domElement);
  renderer.domElement.style.cursor = 'grab';

  const tooltip = document.createElement('div');
  tooltip.style.cssText = [
    'position:absolute',
    'z-index:20',
    'display:none',
    'min-width:min(240px, calc(100vw - 32px))',
    'max-width:min(300px, calc(100vw - 32px))',
    'padding:8px 10px',
    'border:1px solid rgba(148,163,184,0.35)',
    'border-radius:8px',
    'background:rgba(15,23,42,0.92)',
    'box-shadow:0 12px 30px rgba(15,23,42,0.22)',
    'color:white',
    'font:11px/1.35 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    'pointer-events:none',
    'white-space:nowrap',
    'transform:translate(12px, -50%)',
  ].join(';');
  globeContainer?.appendChild(tooltip);

  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xcccccc, Math.PI), new THREE.DirectionalLight(0xffffff, 0.6 * Math.PI));

  const camera = new THREE.PerspectiveCamera(undefined, renderWidth / renderHeight, undefined, undefined);
  camera.position.z = 300;

  const tbControls = new TrackballControls(camera, renderer.domElement);
  Object.assign(tbControls, {
    minDistance: 101,
    rotateSpeed: 5,
    zoomSpeed: 0.8,
  });

  const globeObject = new THREE.Object3D();
  globeObject.add(Globe);
  scene.add(globeObject);

  const clock = new THREE.Clock();
  let autoRotate = true;
  tbControls.addEventListener('start', () => (autoRotate = false));

  function animate() {
    tbControls.update();
    if (autoRotate) globeObject.rotation.y += 0.1 * clock.getDelta();
    renderer.render(scene, camera);
    if (typeof window !== 'undefined') window.requestAnimationFrame(animate);
  }
  if (typeof window !== 'undefined') animate();

  const coordKey = (lat, lng) => `${lat.toFixed(3)},${lng.toFixed(3)}`;
  const serverRingIndex = new Map();
  const pointIndex = new Map();
  let deferPointRefresh = false;
  let needsPointRefresh = false;

  function refreshPoints() {
    if (deferPointRefresh) {
      needsPointRefresh = true;
      return;
    }
    Globe.pointsData(points.slice());
  }

  function refreshRings() {
    Globe.ringsData(rings.slice());
  }

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function setTooltip(point, event) {
    if (!tooltip || !globeContainer || !point?.route) return;
    const rect = globeContainer.getBoundingClientRect();
    tooltip.replaceChildren();

    const title = document.createElement('div');
    const isServerPoint = point.kind === 'server';
    title.textContent = isServerPoint ? 'Destination' : 'Source';
    title.style.cssText = 'margin-bottom:5px;color:rgba(226,232,240,0.72);font-size:10px;text-transform:uppercase;letter-spacing:0.08em';
    tooltip.appendChild(title);

    for (const [label, value] of [
      ['from', point.route.from],
      ['to', point.route.to],
      ...(point.route.visitedAt ? [['visited', point.route.visitedAt]] : []),
    ]) {
      const row = document.createElement('div');
      row.style.whiteSpace = 'nowrap';
      const labelEl = document.createElement('span');
      labelEl.textContent = label;
      labelEl.style.color = 'rgba(226,232,240,0.7)';
      row.append(labelEl, ` ${value}`);
      tooltip.appendChild(row);
    }

    tooltip.style.left = `${event.clientX - rect.left}px`;
    tooltip.style.top = `${event.clientY - rect.top}px`;
    tooltip.style.display = 'block';
  }

  function hideTooltip() {
    if (tooltip) tooltip.style.display = 'none';
    renderer.domElement.style.cursor = 'grab';
  }

  function findPointIntersection(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);

    const hit = raycaster.intersectObject(globeObject, true).find((intersection) => intersection.object.__globeObjType === 'point');
    return hit?.object?.__data ?? null;
  }

  renderer.domElement.addEventListener('pointermove', (event) => {
    const point = findPointIntersection(event);
    if (point?.route) {
      renderer.domElement.style.cursor = 'pointer';
      setTooltip(point, event);
    } else {
      hideTooltip();
    }
  });
  renderer.domElement.addEventListener('pointerleave', hideTooltip);

  function upsertPoint(kind, lat, lng, color, radius, altitude, route = null, pointKey = null) {
    const key = pointKey ?? `${kind}:${coordKey(lat, lng)}`;
    const existing = pointIndex.get(key);
    if (existing) {
      existing.seenAt = Date.now();
      if (route) existing.route = route;
    } else {
      const point = { key, kind, lat, lng, color, radius, altitude, route, seenAt: Date.now() };
      pointIndex.set(key, point);
      points.push(point);
    }

    points.sort((a, b) => {
      if (a.kind !== b.kind) return a.kind === 'server' ? -1 : 1;
      return b.seenAt - a.seenAt;
    });
    while (points.length > MAX_POINTS) {
      const old = points.pop();
      pointIndex.delete(old.key);
    }
    refreshPoints();
  }

  function addVisitorPulse(lat, lng) {
    // Do not dedupe source pulses. Repeated visits from the same place should
    // visibly restart the source animation instead of disappearing into an
    // existing marker.
    const createdAt = Date.now();
    rings.push(
      {
        lat,
        lng,
        color: VISITOR_CORE_RING_COLOR,
        maxRadius: 3.8,
        speed: 2.6,
        repeat: 260,
        _kind: 'visitor',
        _createdAt: createdAt,
      },
      {
        lat,
        lng,
        color: VISITOR_RING_COLOR,
        maxRadius: 11,
        speed: 4.6,
        repeat: 320,
        _kind: 'visitor',
        _createdAt: createdAt,
      },
    );

    let visitorCount = 0;
    for (let i = rings.length - 1; i >= 0; i--) {
      if (rings[i]._kind !== 'visitor') continue;
      visitorCount += 1;
      if (visitorCount > MAX_VISITOR_PULSES) rings.splice(i, 1);
    }
    refreshRings();
  }

  function ensureServerRing(lat, lng) {
    const key = coordKey(lat, lng);
    if (serverRingIndex.has(key)) return;
    const ring = {
      lat,
      lng,
      color: SERVER_RING_COLOR,
      maxRadius: 5,
      speed: 1.8,
      repeat: 900,
      _kind: 'server',
    };
    serverRingIndex.set(key, ring);
    rings.push(ring);
    refreshRings();
  }

  function addVisit(visit, render = true) {
    if (!visit?.source || !visit?.server) return;
    const route = {
      from: formatSource(visit.source),
      to: formatServer(visit.server),
      visitedAt: formatVisitTime(visit.ts),
    };
    arcs.push({
      startLat: visit.source.lat,
      startLng: visit.source.lng,
      endLat: visit.server.lat,
      endLng: visit.server.lng,
      color: ARC_COLOR_GRADIENT,
      stroke: 0.45,
      altitudeScale: 0.45,
      dashLength: 0.4,
      dashGap: 2,
      dashInitialGap: 1,
      animateTime: ARC_FLIGHT_MS,
    });
    while (arcs.length > MAX_ARCS) arcs.shift();
    // three-globe loops the dash animation indefinitely while the arc stays
    // in arcsData — so simply leaving it there gives an infinite flow.
    if (render) Globe.arcsData(arcs.slice());

    upsertPoint('visitor', visit.source.lat, visit.source.lng, SOURCE_POINT_COLOR, 1.25, 0.045, route);
    upsertPoint('server', visit.server.lat, visit.server.lng, SERVER_POINT_COLOR, 0.55, 0.025, route);
    addVisitorPulse(visit.source.lat, visit.source.lng);
    ensureServerRing(visit.server.lat, visit.server.lng);
  }

  function addVisits(visits) {
    deferPointRefresh = true;
    needsPointRefresh = false;
    for (const visit of visits) addVisit(visit, false);
    deferPointRefresh = false;
    if (needsPointRefresh) refreshPoints();
    Globe.arcsData(arcs.slice());
    refreshRings();
  }

  function setServerBeacon(server) {
    if (!server) return;
    upsertPoint('server', server.lat, server.lng, SERVER_POINT_COLOR, 0.55, 0.025);
    ensureServerRing(server.lat, server.lng);
  }

  return { addVisit, addVisits, setServerBeacon };
}
