"use client";

import {
  useEffect,
  useRef,
  useCallback,
} from "react";

import * as THREE from "three";
import { GLTFLoader } from "three-stdlib";

import {
  VRM,
  VRMLoaderPlugin,
  VRMHumanBoneName,
  VRMExpressionPresetName,
} from "@pixiv/three-vrm";

interface VRMAvatarProps {
  isSpeaking: boolean;
}

export default function VRMAvatar({
  isSpeaking,
}: VRMAvatarProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(null);

  const vrmRef =
    useRef<VRM | null>(null);

  const rendererRef =
    useRef<THREE.WebGLRenderer | null>(
      null
    );

  const sceneRef =
    useRef<THREE.Scene | null>(null);

  const cameraRef =
    useRef<THREE.PerspectiveCamera | null>(
      null
    );

  const animationFrameRef =
    useRef<number | null>(null);

  const mouthIntervalRef =
    useRef<ReturnType<
      typeof setInterval
    > | null>(null);

  const blinkIntervalRef =
    useRef<ReturnType<
      typeof setInterval
    > | null>(null);

  const blinkTimeoutRef =
    useRef<ReturnType<
      typeof setTimeout
    > | null>(null);

  const mouseRef = useRef({
    x: 0,
    y: 0,
  });

  const stopMouthAnimation =
    useCallback(() => {
      if (mouthIntervalRef.current) {
        clearInterval(
          mouthIntervalRef.current
        );
        mouthIntervalRef.current =
          null;
      }

      const vrm = vrmRef.current;

      if (
        vrm?.expressionManager
      ) {
        vrm.expressionManager.setValue(
          VRMExpressionPresetName.Aa,
          0
        );
        vrm.expressionManager.setValue(
          VRMExpressionPresetName.Oh,
          0
        );
        vrm.expressionManager.setValue(
          VRMExpressionPresetName.Ee,
          0
        );
      }
    }, []);

  const startMouthAnimation =
    useCallback(() => {
      stopMouthAnimation();

      const vrm = vrmRef.current;

      if (
        !vrm?.expressionManager
      ) {
        return;
      }

      mouthIntervalRef.current =
        setInterval(() => {
          const currentVrm =
            vrmRef.current;

          if (
            !currentVrm ||
            !currentVrm.expressionManager
          ) {
            return;
          }

          const aa =
            0.35 +
            Math.random() * 0.45;

          const oh =
            0.08 +
            Math.random() * 0.18;

          const ee =
            Math.random() * 0.12;

          currentVrm.expressionManager.setValue(
            VRMExpressionPresetName.Aa,
            aa
          );

          currentVrm.expressionManager.setValue(
            VRMExpressionPresetName.Oh,
            oh
          );

          currentVrm.expressionManager.setValue(
            VRMExpressionPresetName.Ee,
            ee
          );
        }, 100);
    }, [stopMouthAnimation]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const container =
      containerRef.current;

    const width =
      container.clientWidth || 1000;

    const height =
      container.clientHeight || 600;

    const scene =
      new THREE.Scene();

    sceneRef.current = scene;

    const camera =
      new THREE.PerspectiveCamera(
        30,
        width / height,
        0.1,
        1000
      );

    camera.position.set(
      0,
      1.3,
      4.8
    );

    camera.lookAt(0, 1.1, 0);

    cameraRef.current = camera;

    const renderer =
      new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
      });

    renderer.setSize(
      width,
      height
    );

    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio,
        2
      )
    );

    renderer.setClearColor(
      0x000000,
      0
    );

    rendererRef.current =
      renderer;

    container.innerHTML = "";
    container.appendChild(
      renderer.domElement
    );

    // Lights
    const keyLight =
      new THREE.DirectionalLight(
        0xffffff,
        1.5
      );
    keyLight.position.set(
      1,
      2,
      3
    );
    scene.add(keyLight);

    const fillLight =
      new THREE.DirectionalLight(
        0xffffff,
        1.0
      );
    fillLight.position.set(
      -1,
      1,
      2
    );
    scene.add(fillLight);

    const ambientLight =
      new THREE.AmbientLight(
        0xffffff,
        1.8
      );
    scene.add(ambientLight);

    // Load VRM
    const loader =
      new GLTFLoader();

    loader.register(
      (parser) =>
        new VRMLoaderPlugin(
          parser as never
        ) as never
    );

    loader.load(
      "/avatar/shant_avatar.vrm",
      (gltf) => {
        const vrm =
          gltf.userData.vrm as VRM;

        if (!vrm) {
          console.error(
            "❌ VRM not found in loaded file"
          );
          return;
        }

        const model =
          vrm.scene;

        model.traverse(
          (obj: THREE.Object3D) => {
            obj.frustumCulled = false;
          }
        );

        // Face front
        model.rotation.y = 0;

        // -------- FIX FULL BODY FIT --------
        const box =
          new THREE.Box3().setFromObject(
            model
          );

        const size =
          new THREE.Vector3();

        const center =
          new THREE.Vector3();

        box.getSize(size);
        box.getCenter(center);

        // Smaller target height so full body fits
        const targetHeight = 1.8;

        if (size.y > 0) {
          const scale =
            targetHeight / size.y;
          model.scale.setScalar(scale);
        }

        // recompute after scaling
        const scaledBox =
          new THREE.Box3().setFromObject(
            model
          );

        const scaledSize =
          new THREE.Vector3();

        const scaledCenter =
          new THREE.Vector3();

        scaledBox.getSize(
          scaledSize
        );
        scaledBox.getCenter(
          scaledCenter
        );

        // center avatar horizontally
        model.position.x =
          -scaledCenter.x;

        // place feet on bottom with little padding
        model.position.y =
          -scaledBox.min.y - 0.05;

        model.position.z = 0;

        scene.add(model);
        vrmRef.current = vrm;

        // subtle face expression
        if (
          vrm.expressionManager
        ) {
          vrm.expressionManager.setValue(
            VRMExpressionPresetName.Happy,
            0.12
          );
        }

        // Camera framing for full body
        camera.position.set(
          0,
          scaledSize.y * 0.62,
          4.8
        );

        camera.lookAt(
          0,
          scaledSize.y * 0.5,
          0
        );

        console.log(
          "✅ VRM Avatar Loaded"
        );
      },
      undefined,
      (error) => {
        console.error(
          "❌ Failed to load VRM:",
          error
        );
      }
    );

    // Mouse move
    const handleMouseMove = (
      e: MouseEvent
    ) => {
      const rect =
        container.getBoundingClientRect();

      const x =
        (e.clientX - rect.left) /
          rect.width -
        0.5;

      const y =
        (e.clientY - rect.top) /
          rect.height -
        0.5;

      mouseRef.current = {
        x,
        y,
      };
    };

    container.addEventListener(
      "mousemove",
      handleMouseMove
    );

    // Resize
    const handleResize = () => {
      const renderer =
        rendererRef.current;

      const cam =
        cameraRef.current;

      const currentContainer =
        containerRef.current;

      if (
        !renderer ||
        !cam ||
        !currentContainer
      ) {
        return;
      }

      const newWidth =
        currentContainer.clientWidth ||
        1000;

      const newHeight =
        currentContainer.clientHeight ||
        600;

      renderer.setSize(
        newWidth,
        newHeight
      );

      cam.aspect =
        newWidth / newHeight;

      cam.updateProjectionMatrix();
    };

    window.addEventListener(
      "resize",
      handleResize
    );

    // Blink animation
    blinkIntervalRef.current =
      setInterval(() => {
        const vrm =
          vrmRef.current;

        if (
          !vrm ||
          !vrm.expressionManager
        ) {
          return;
        }

        vrm.expressionManager.setValue(
          VRMExpressionPresetName.Blink,
          1
        );

        blinkTimeoutRef.current =
          setTimeout(() => {
            if (
              vrmRef.current
                ?.expressionManager
            ) {
              vrmRef.current.expressionManager.setValue(
                VRMExpressionPresetName.Blink,
                0
              );
            }
          }, 140);
      }, 3000);

    // Animation loop
    const timer =
      new THREE.Timer();

    timer.connect(document);
    timer.reset();

    const animate = () => {
      animationFrameRef.current =
        requestAnimationFrame(
          animate
        );

      timer.update();

      const vrm =
        vrmRef.current;

      if (vrm) {
        vrm.update(
          timer.getDelta()
        );

        const neck =
          vrm.humanoid?.getNormalizedBoneNode(
            VRMHumanBoneName.Neck
          );

        if (neck) {
          neck.rotation.y =
            mouseRef.current.x * 0.25;

          neck.rotation.x =
            -mouseRef.current.y * 0.12;
        }

        vrm.expressionManager?.update();
      }

      renderer.render(
        scene,
        camera
      );
    };

    animate();

    return () => {
      container.removeEventListener(
        "mousemove",
        handleMouseMove
      );

      window.removeEventListener(
        "resize",
        handleResize
      );

      if (
        animationFrameRef.current
      ) {
        cancelAnimationFrame(
          animationFrameRef.current
        );
        animationFrameRef.current =
          null;
      }

      if (
        blinkIntervalRef.current
      ) {
        clearInterval(
          blinkIntervalRef.current
        );
        blinkIntervalRef.current =
          null;
      }

      if (
        blinkTimeoutRef.current
      ) {
        clearTimeout(
          blinkTimeoutRef.current
        );
        blinkTimeoutRef.current =
          null;
      }

      stopMouthAnimation();

      if (
        vrmRef.current?.scene &&
        sceneRef.current
      ) {
        sceneRef.current.remove(
          vrmRef.current.scene
        );
      }

      vrmRef.current = null;

      if (rendererRef.current) {
        rendererRef.current.dispose();
        rendererRef.current = null;
      }

      if (
        container.contains(
          renderer.domElement
        )
      ) {
        container.removeChild(
          renderer.domElement
        );
      }

      sceneRef.current = null;
      cameraRef.current = null;
    };
  }, [stopMouthAnimation]);

  useEffect(() => {
    if (isSpeaking) {
      startMouthAnimation();
    } else {
      stopMouthAnimation();
    }

    return () => {
      stopMouthAnimation();
    };
  }, [
    isSpeaking,
    startMouthAnimation,
    stopMouthAnimation,
  ]);

  return (
    <div
      ref={containerRef}
      className="
        w-full
        h-[520px]
        rounded-3xl
        overflow-hidden
        bg-gradient-to-b
        from-[#F8F8FB]
        to-white
      "
    />
  );
}