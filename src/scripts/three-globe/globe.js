import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import * as THREE from 'three';
import ThreeGlobe from 'three-globe';
import countriesData from './countries.js';
import config from '../../config.json';

export const { globeViewWidth: renderWidth, globeViewHeight: renderHeight } = config;

const ARC_FLIGHT_MS = 2200;
const MAX_ARCS = 24;
const MAX_VISITOR_PULSES = 32;
const MAX_POINTS = 32;

// Bright cyan → soft white gradient for the glowing trail.
const ARC_COLOR_GRADIENT = ['rgba(56,189,248,0.95)', 'rgba(244,255,255,1)', 'rgba(56,189,248,0.95)'];
const SOURCE_POINT_COLOR = 'rgba(34, 211, 238, 0.98)';
const SERVER_POINT_COLOR = 'rgba(244, 114, 182, 0.9)';
const SERVER_RING_COLOR = (t) => `rgba(244, 114, 182, ${0.75 * (1 - t)})`;
const VISITOR_RING_COLOR = (t) => `rgba(34, 211, 238, ${1 - t})`;
const VISITOR_CORE_RING_COLOR = (t) => `rgba(255, 255, 255, ${0.9 * (1 - t)})`;

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
    .hexPolygonColor(() => {
      const shade = Math.floor(Math.random() * 115 + 140); // Range: 100-255
      return `rgb(${shade},${shade},${shade})`;
    })
    .hexPolygonAltitude(0.001)
    .globeMaterial(new THREE.MeshPhongMaterial({ opacity: 0.1, transparent: true }))
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
    .arcColor(() => ARC_COLOR_GRADIENT)
    .arcStroke(0.45)
    .arcAltitudeAutoScale(0.45)
    .arcDashLength(0.4)
    .arcDashGap(2)
    .arcDashInitialGap(1)
    .arcDashAnimateTime(ARC_FLIGHT_MS)
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
  document.getElementById('globe-point-cloud').appendChild(renderer.domElement);

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

  const globeContainer = new THREE.Object3D();
  globeContainer.add(Globe);
  scene.add(globeContainer);

  const clock = new THREE.Clock();
  let autoRotate = true;
  tbControls.addEventListener('start', () => (autoRotate = false));

  function animate() {
    tbControls.update();
    if (autoRotate) globeContainer.rotation.y += 0.1 * clock.getDelta();
    renderer.render(scene, camera);
    if (typeof window !== 'undefined') window.requestAnimationFrame(animate);
  }
  if (typeof window !== 'undefined') animate();

  const coordKey = (lat, lng) => `${lat.toFixed(3)},${lng.toFixed(3)}`;
  const serverRingIndex = new Map();
  const pointIndex = new Map();

  function refreshRings() {
    Globe.ringsData(rings.slice());
  }

  function upsertPoint(kind, lat, lng, color, radius, altitude) {
    const key = `${kind}:${coordKey(lat, lng)}`;
    const existing = pointIndex.get(key);
    if (existing) {
      existing.seenAt = Date.now();
    } else {
      const point = { kind, lat, lng, color, radius, altitude, seenAt: Date.now() };
      pointIndex.set(key, point);
      points.push(point);
    }

    points.sort((a, b) => {
      if (a.kind !== b.kind) return a.kind === 'server' ? -1 : 1;
      return b.seenAt - a.seenAt;
    });
    while (points.length > MAX_POINTS) {
      const old = points.pop();
      pointIndex.delete(`${old.kind}:${coordKey(old.lat, old.lng)}`);
    }
    Globe.pointsData(points.slice());
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

  function addVisit(visit) {
    if (!visit?.source || !visit?.server) return;
    arcs.push({
      startLat: visit.source.lat,
      startLng: visit.source.lng,
      endLat: visit.server.lat,
      endLng: visit.server.lng,
    });
    while (arcs.length > MAX_ARCS) arcs.shift();
    // three-globe loops the dash animation indefinitely while the arc stays
    // in arcsData — so simply leaving it there gives an infinite flow.
    Globe.arcsData(arcs.slice());

    upsertPoint('visitor', visit.source.lat, visit.source.lng, SOURCE_POINT_COLOR, 1.25, 0.045);
    upsertPoint('server', visit.server.lat, visit.server.lng, SERVER_POINT_COLOR, 0.55, 0.025);
    addVisitorPulse(visit.source.lat, visit.source.lng);
    ensureServerRing(visit.server.lat, visit.server.lng);
  }

  function setServerBeacon(server) {
    if (!server) return;
    upsertPoint('server', server.lat, server.lng, SERVER_POINT_COLOR, 0.55, 0.025);
    ensureServerRing(server.lat, server.lng);
  }

  return { addVisit, setServerBeacon };
}
