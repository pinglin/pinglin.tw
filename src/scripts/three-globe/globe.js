import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import * as THREE from 'three';
import ThreeGlobe from 'three-globe';
import countriesData from './countries.js';
import config from '../../config.json';

export const { globeViewWidth: renderWidth, globeViewHeight: renderHeight } = config;

const ARC_FLIGHT_MS = 2200;
const MAX_ARCS = 24;
const MAX_VISITOR_RINGS = 24;

// Bright cyan → soft white gradient for the glowing trail.
const ARC_COLOR_GRADIENT = ['rgba(56,189,248,0.95)', 'rgba(244,255,255,1)', 'rgba(56,189,248,0.95)'];
const SERVER_RING_COLOR = (t) => `rgba(244, 114, 182, ${1 - t})`;
const VISITOR_RING_COLOR = (t) => `rgba(56, 189, 248, ${1 - t})`;

export function initGlobe() {
  const arcs = [];
  const rings = [];

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
    .ringMaxRadius(4)
    .ringPropagationSpeed(2.5)
    .ringRepeatPeriod(700);

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

  // Dedupe key for rings so repeated polls don't pile up overlapping rings at
  // the same coordinate.
  const ringKey = (lat, lng) => `${lat.toFixed(3)},${lng.toFixed(3)}`;
  const ringIndex = new Map();

  function ensureRing(lat, lng, color) {
    const key = ringKey(lat, lng);
    if (ringIndex.has(key)) return;
    const ring = { lat, lng, color, _kind: color === SERVER_RING_COLOR ? 'server' : 'visitor' };
    ringIndex.set(key, ring);
    rings.push(ring);

    // Cap visitor-side rings; the single server ring is sticky.
    let visitorCount = 0;
    for (let i = rings.length - 1; i >= 0; i--) {
      if (rings[i]._kind !== 'visitor') continue;
      visitorCount += 1;
      if (visitorCount > MAX_VISITOR_RINGS) {
        const old = rings.splice(i, 1)[0];
        ringIndex.delete(ringKey(old.lat, old.lng));
      }
    }
    Globe.ringsData(rings.slice());
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

    ensureRing(visit.source.lat, visit.source.lng, VISITOR_RING_COLOR);
    ensureRing(visit.server.lat, visit.server.lng, SERVER_RING_COLOR);
  }

  function setServerBeacon(server) {
    if (!server) return;
    ensureRing(server.lat, server.lng, SERVER_RING_COLOR);
  }

  return { addVisit, setServerBeacon };
}
