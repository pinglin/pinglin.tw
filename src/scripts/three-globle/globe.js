import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import * as THREE from 'three';
import ThreeGlobe from 'three-globe';
import countriesData from './countries.js';
import config from '../../config.json';

export const { globeViewWidth: renderWidth, globeViewHeight: renderHeight } =
  config;

export function initGlobe() {
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
    .globeMaterial(
      new THREE.MeshPhongMaterial({ opacity: 0.1, transparent: true }),
    );

  const renderer = new THREE.WebGLRenderer({ alpha: true });
  renderer.setSize(renderWidth, renderHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.getElementById('globe-point-cloud').appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.add(
    new THREE.AmbientLight(0xcccccc, Math.PI),
    new THREE.DirectionalLight(0xffffff, 0.6 * Math.PI),
  );

  const camera = new THREE.PerspectiveCamera(
    undefined,
    renderWidth / renderHeight,
    undefined,
    undefined,
  );
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

  function animate() {
    tbControls.update();
    globeContainer.rotation.y -= 0.12 * clock.getDelta();
    renderer.render(scene, camera);
    if (typeof window !== 'undefined') window.requestAnimationFrame(animate);
  }
  if (typeof window !== 'undefined') animate();
}
