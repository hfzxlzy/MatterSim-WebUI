# 调用 json 库格式化传入文件
import json
# 调用 pathlib 库解析文件路径
from pathlib import Path
# 导入 Three.js 引擎单文件位置
from webui.core.env import THREEJS_BUNDLE

# 结构模型显示html生成器
def Brillouin_renderer_html(
    Bz,    # 布里渊区数据
    mode="auto",    # auto/local/cdn
    threejs_local="/app/static/3jsmain/three.module.js",    # local_path
    addons_local="/app/static/3addons/",    # local_path
    threejs_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/build/three.module.js",    # cdn_url
    addons_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/examples/jsm/",    # cdn_url
):
    """
    返回一个 <iframe>，里面用 Three.js r184 (ESM) 渲染 ASE 结构。
    """
    # 格式化结构及声子元数据
    bz_js = json.dumps(Bz)
    # js结构信息块
    data_html = f"""
  <script>  
    const BZone = {bz_js};
  </script>
"""
    # 3js调用信息头
    if mode == "local":
        load_js = f"""
    <script type="importmap">
    {{
      "imports":{{
        "three": "{threejs_local}",
        "three/addons/": "{addons_local}"
      }}
    }}
    </script>
    <script type="module">
      import * as THREE from 'three';
      import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
      import {{ ConvexGeometrys }} from 'three/addons/geometries/ConvexGeometry.js';

      console.log("THREE =", THREE);
      console.log("OrbitControls =", OrbitControls);
      console.log("ConvexGeometry =", ConvexGeometry);
"""
    elif mode == "cdn":
        load_js = f"""
    <script type="importmap">
    {{
      "imports":{{
        "three": "{threejs_url}",
        "three/addons/": "{addons_url}"
      }}
    }}
    </script>
    <script type="module">
      import * as THREE from 'three';
      import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
      import {{ ConvexGeometrys }} from 'three/addons/geometries/ConvexGeometry.js';

      console.log("THREE =", THREE);
      console.log("OrbitControls =", OrbitControls);
      console.log("ConvexGeometry =", ConvexGeometry);
"""
    else:
        # 读取本地 Three.js 源码 
        threejs_bundle = Path(THREEJS_BUNDLE).read_text(encoding='utf-8')
        load_js = f"""
    <script type="importmap">
      {{
        "imports":{{
          "three": "{threejs_url}",
          "three/addons/": "{addons_url}"
        }}
      }}
    </script>

    <script type="module">  
      console.log('🚀 尝试从 CDN 加载 Three.js...');
      let THREE, OrbitControls, ConvexGeometry;
      // ============ CDN 加载（带超时） ============
      const CDN_TIMEOUT = 1500; // 1.5秒超时
      try {{
        // 创建超时 Promise
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('CDN 加载超时')), CDN_TIMEOUT)
        );
        // CDN 加载 Promise
        const cdnPromise = Promise.all([
          import("three"),
          import("three/addons/controls/OrbitControls.js"),
          import("three/addons/geometries/ConvexGeometry.js")
        ]);
        // 竞速：谁先完成用谁
        const results = await Promise.race([cdnPromise, timeoutPromise]);
        // 如果 CDN 成功
        const [threeModule, controlsModule, convexModule] = results;
        THREE = threeModule;
        OrbitControls = controlsModule.OrbitControls;
        ConvexGeometry = convexModule.ConvexGeometry;
        console.log("🌐 CDN Three.js 加载成功");
      }} catch (err) {{  
        console.log('❌ CDN 加载失败，从 Rollup 打包的单文件加载...');
        console.log('错误:', err.message);
        // ============ 注入打包代码 ============
        const bundleCode = {json.dumps(threejs_bundle)};
        // ============ 创建 Blob URL ============
        const bundleURL = URL.createObjectURL(
          new Blob([bundleCode], {{ type: 'application/javascript' }})
        );
        console.log('✅ Blob URL 创建完成');
        // ============ 导入 ============
        // Rollup 打包的 ESM 会导出所有 export * 的内容
        const bundleExports = await import(bundleURL);
        console.log('✅ Three.js 加载成功');
        //console.log('导出内容:', Object.keys(THREE));
        // ============ 提取需要的模块 ============
        // Rollup 打包后，所有 export * 的内容都在 THREE 对象上
        ({{ OrbitControls, ConvexGeometry }} = bundleExports);
        // THREE 可能是 bundleExports 本身，也可能在 default 里
        THREE = bundleExports.default || bundleExports;
      }}
        console.log('THREE =', THREE);
        console.log('OrbitControls =', OrbitControls);
        console.log('ConvexGeometry =', ConvexGeometry);
"""
    # 拼接完整html文件
    inner_html = f"""
{html_start}
<body>
<div id="main-container">
  {data_html}
  {js_renderer(load_js)}
</div>
</body>
</html>
"""
    return inner_html

# HTML文件头生成器
html_start = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>布里渊区</title>
<style>
/* CSS 部分 */
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  body {{
    background: #f8f8f8;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    font-family: "Microsoft YaHei", sans-serif;
  }}
  #viewer {{
    width: 100vw;
    height: 100vh;
    display: block;
    background: #f8f8f8;
  }}
  /* 确保canvas填满容器且不溢出 */
  #viewer canvas {{
    display: block;
    width: 100% !important;
    height: 100% !important;
    border: 1px solid #222;   /* 黑框，符合原意 */
  }}
</style>
</head>
"""

# 结构模型渲染及交互块生成器
def js_renderer(load_js):
    js_renderer = f"""
  <div id="viewer">
    {load_js}
    // === 通用工具函数 ===
    // 通用文字标签函数
    function makeLabel(text, position, scene, options = {{}}) {{
      const fontSize = options.fontSize || 48;     // 字体大小（越大越清晰）
      const color = options.color || "black";      // 字体颜色
      const scale = options.scale || 0.15;         // Sprite 缩放大小
      const dpr = window.devicePixelRatio || 1;  // 高 DPI 支持
      // 创建 canvas
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      // 预估文字宽度（先设置字体）
      ctx.font = `${{fontSize}}px Arial`;
      const textWidth = ctx.measureText(text).width;
      // 使用高 DPI 分辨率
      canvas.width = textWidth + 20 * dpr;
      canvas.height = (fontSize + 20) * dpr;
      // 设置 canvas 尺寸（必须在绘制前设置）
      canvas.width = textWidth + 20;
      canvas.height = fontSize + 20;
      // 重新设置字体（因为设置 canvas 尺寸会清空上下文）
      ctx.font = `${{fontSize}}px Arial`;
      ctx.fillStyle = color;
      ctx.fillText(text, 10, fontSize);
      // 生成纹理
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
      // Sprite 材质
      const spriteMaterial = new THREE.SpriteMaterial({{
        map: texture,
        transparent: true,
        depthTest: false,   // 禁用深度，防止遮挡
        depthWrite: false
      }});
      const sprite = new THREE.Sprite(spriteMaterial);
      // 控制文字缩放到 Three.js 世界尺寸
      sprite.scale.set(scale * (canvas.width /canvas.height), scale, 1);
      // 设置位置
      sprite.position.copy(position);
      // 加入场景
      scene.add(sprite);

      return sprite;
    }}
    // 下角标转换函数
    function toSubscript(label) {{
      return label.replace(/_(\d+)/g, (_, num) =>
        num.split("").map(d => "₀₁₂₃₄₅₆₇₈₉"[d]).join("")
      );
    }}
    // 分数坐标到倒格矢笛卡尔坐标转换函数
    function fracToCart(coord, B) {{
      return new THREE.Vector3(
        coord[0] * B[0][0] + coord[1] * B[1][0] + coord[2] * B[2][0],
        coord[0] * B[0][1] + coord[1] * B[1][1] + coord[2] * B[2][1],
        coord[0] * B[0][2] + coord[1] * B[1][2] + coord[2] * B[2][2]
      );
    }}

    // === 初始化场景 ===
    // 创建 Three.js 的世界容器
    const scene = new THREE.Scene();
    // 设置背景颜色
    scene.background = new THREE.Color(0xffffff);
    // 创建相机
    const camera = new THREE.PerspectiveCamera(
      45,   //视野角度（FOV）
      window.innerWidth / window.innerHeight,   //宽高比
      0.01,   //近裁剪面
      100   //远裁剪面
    );
    // 相机位置
    camera.position.set(0.35, 0.35, 0.35);
    // 创建WebGLRenderer渲染引擎(antialias: true 开启抗锯齿)
    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    // 设置画布大小
    renderer.setSize(window.innerWidth, window.innerHeight);
    // 把渲染器的 canvas 放进 HTML
    document.getElementById("viewer").appendChild(renderer.domElement);

    // === 控制器 ===
    // OrbitControls：鼠标左键旋转、鼠标右键、平移滚轮缩放
    const controls = new OrbitControls(camera, renderer.domElement);
    // 阻尼效果，让旋转/缩放更平滑
    controls.enableDamping = true;

    // === 自动适配尺寸（防止放大后模糊） ===
    const viewer = document.getElementById("viewer");
    const ro = new ResizeObserver(entries => {{
      const rect = entries[0].contentRect;
      renderer.setSize(rect.width, rect.height, false);
      // 真实像素比
      const dpr = rect.width / renderer.domElement.width;
      renderer.setPixelRatio(dpr);
      camera.aspect = rect.width / rect.height;
      camera.updateProjectionMatrix();
    }});
    // 观察 viewer 容器，而不是 window（避免 sandbox 污染）
    ro.observe(viewer);

    // === 坐标轴 ===
    // 原始笛卡尔坐标轴
    function createArrowAxes(length = 1) {{
      const group = new THREE.Group();
      const headLength = length * 0.1;   // 箭头头部长度
      const headWidth  = length * 0.05;   // 箭头头部宽度
      // X 轴（红）
      const xArrow = new THREE.ArrowHelper(
        new THREE.Vector3(1, 0, 0),      // 方向
        new THREE.Vector3(0, 0, 0),      // 起点
        length,                          // 长度
        0xd59985,                        // 颜色
        headLength,
        headWidth
      );
      group.add(xArrow);
      makeLabel("x", new THREE.Vector3(length * 1.05, 0, 0), scene, {{
        fontSize: 80,
        scale: 0.03,
        color: "#94695c"
      }});
      // Y 轴（绿）
      const yArrow = new THREE.ArrowHelper(
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(0, 0, 0),
        length,
        0xc1d585,
        headLength,
        headWidth
      );
      group.add(yArrow);
      makeLabel("y", new THREE.Vector3(0, length * 1.05, 0), scene, {{
        fontSize: 80,
        scale: 0.03,
        color: "#2c8358"
      }});
      // Z 轴（蓝）
      const zArrow = new THREE.ArrowHelper(
        new THREE.Vector3(0, 0, 1),
        new THREE.Vector3(0, 0, 0),
        length,
        0x8599d5,
        headLength,
        headWidth
      );
      group.add(zArrow);
      makeLabel("z", new THREE.Vector3(0, 0, length * 1.05), scene, {{
        fontSize: 80,
        scale: 0.03,
        color: "#5b6892"
      }});
      return group;
    }}
    // 倒格矢轴
    function addReciprocalAxes(scene, BZone) {{
      const b1 = new THREE.Vector3(...BZone.reciprocal_lattice[0]);
      const b2 = new THREE.Vector3(...BZone.reciprocal_lattice[1]);
      const b3 = new THREE.Vector3(...BZone.reciprocal_lattice[2]);
      const origin = new THREE.Vector3(0, 0, 0);
      // 固定箭头头部大小
      const headLength = 0.02;
      const headWidth  = 0.01;
      // b1
      const arrow1 = new THREE.ArrowHelper(
        b1.clone().normalize(),  // 方向
        origin,                  // 起点
        b1.length(),             // 箭头总长度
        0xff0000,                // 颜色（红色）
        headLength,              // 箭头头部长度
        headWidth                // 箭头头部宽度
      );
      scene.add(arrow1);
      makeLabel("b1", b1.clone().multiplyScalar(1.05), scene, {{fontSize: 100, scale: 0.02, color: "black"}});
      // b2
      const arrow2 = new THREE.ArrowHelper(
        b2.clone().normalize(),
        origin,
        b2.length(),
        0x00ff00,                // 颜色（绿色）
        headLength,              // 箭头头部长度
        headWidth                // 箭头头部宽度
      );
      scene.add(arrow2);
      makeLabel("b2", b2.clone().multiplyScalar(1.05), scene, {{fontSize: 100, scale: 0.02, color: "black"}});
      // b3
      const arrow3 = new THREE.ArrowHelper(
        b3.clone().normalize(),
        origin,
        b3.length(),
        0x0000ff,                // 颜色（蓝色）
        headLength,              // 箭头头部长度
        headWidth                // 箭头头部宽度
      );
      scene.add(arrow3);
      makeLabel("b3", b3.clone().multiplyScalar(1.05), scene, {{fontSize: 100, scale: 0.02, color: "black"}});
    }}
    // 调用
    scene.add(createArrowAxes(0.2));
    addReciprocalAxes(scene, BZone);

    // === 将 BZ 顶点转成 THREE.Vector3 ===
    const bzVerts = BZone.bz_vertices.map(v => new THREE.Vector3(v[0], v[1], v[2]));

    // === 构造布里渊区凸包 ===
    const bzGeometry = new ConvexGeometry(bzVerts);

    // === 材质 ===
    const bzMaterial = new THREE.MeshPhongMaterial({{
      color: 0x66aaff,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide
    }});

    // === BZ Mesh ===
    const bzMesh = new THREE.Mesh(bzGeometry, bzMaterial);
    scene.add(bzMesh);

    // === BZ 线框 ===
    const bzWire = new THREE.LineSegments(
      new THREE.EdgesGeometry(bzGeometry),
      new THREE.LineBasicMaterial({{ color: 0x003388, linewidth: 2 }})
    );
    scene.add(bzWire);

    // === 高对称点（球） ===
    // 先统计每个坐标出现次数
    const posMap = new Map();
    function posKey(v) {{
      return `${{v.x.toFixed(6)}},${{v.y.toFixed(6)}},${{v.z.toFixed(6)}}`;
    }}
    // === 第一次遍历：统计 ===
    for (const p of BZone.highsym_points) {{
      let coord = p.coords;
      if (Array.isArray(coord[0])) coord = coord[0]; // 统一格式
      // 分数坐标 → 倒格矢笛卡尔坐标
      const pos = new THREE.Vector3(
        coord[0] * BZone.reciprocal_lattice[0][0] +
        coord[1] * BZone.reciprocal_lattice[1][0] +
        coord[2] * BZone.reciprocal_lattice[2][0],

        coord[0] * BZone.reciprocal_lattice[0][1] +
        coord[1] * BZone.reciprocal_lattice[1][1] +
        coord[2] * BZone.reciprocal_lattice[2][1],

        coord[0] * BZone.reciprocal_lattice[0][2] +
        coord[1] * BZone.reciprocal_lattice[1][2] +
        coord[2] * BZone.reciprocal_lattice[2][2]
      );
      const key = posKey(pos);
      if (!posMap.has(key)) posMap.set(key, []);
      posMap.get(key).push({{ p, pos }});
    }}
    // === 第二次遍历：绘制球 + 自动分开的标签 ===
    for (const [key, plist] of posMap.entries()) {{
      const basePos = plist[0].pos;  // 球的位置（不动）
      const n = plist.length;
      // 创建球实体
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.005, 10, 10),    // 尺寸
        new THREE.MeshBasicMaterial({{ color: 0xff0000 }})    // 颜色
      );
      sphere.position.copy(basePos);
      scene.add(sphere);
      const radius = 0.015;  // 标签散开的半径
      // === 获取相机视线方向 ===
      const viewDir = new THREE.Vector3();
      camera.getWorldDirection(viewDir);  // 相机朝向
      // === 构造两个与视线垂直的正交向量 ===
      let up = new THREE.Vector3(0, 1, 0);
      // 避免视线接近 Y 轴导致叉乘退化
      if (Math.abs(viewDir.dot(up)) > 0.9) {{
        up = new THREE.Vector3(1, 0, 0);
      }}
      const right = new THREE.Vector3().crossVectors(viewDir, up).normalize();
      const up2   = new THREE.Vector3().crossVectors(right, viewDir).normalize();
      // === 标签去重 ===
      const uniqueLabels = [...new Set(plist.map(x => x.p.label))];
      const m = uniqueLabels.length;
      // === 环形偏移（垂直视线）===
      uniqueLabels.forEach((label, i) => {{
        const angle = (i / m) * Math.PI * 2;
        const offset = right.clone().multiplyScalar(Math.cos(angle) * radius)
                      .add(up2.clone().multiplyScalar(Math.sin(angle) * radius));
        const labelPos = basePos.clone().add(offset);
        makeLabel(toSubscript(label), labelPos, scene, {{
          fontSize: 100,
          scale: 0.02,
          color: "black"
        }});
      }});
    }}
    // === 声子采样路径 ===
    for (let i = 0; i < BZone.highsym_points.length - 1; i+=2) {{
      const p1 = fracToCart(BZone.highsym_points[i].coords, BZone.reciprocal_lattice);
      const p2 = fracToCart(BZone.highsym_points[i+1].coords, BZone.reciprocal_lattice);
      const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
      const length = p1.distanceTo(p2);
      const headLength = 0.020;   // 固定箭头头长度
      const headWidth  = 0.005;   // 固定箭头头宽度
      const arrow = new THREE.ArrowHelper(
        dir,                     // 方向
        p1,                      // 起点
        length,                  // 箭头总长度
        0xffff00,                // 颜色（黄色）
        headLength,
        headWidth
      );
      scene.add(arrow);
    }}

    // === 光源 ===
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const light = new THREE.DirectionalLight(0xffffff, 0.6);
    light.position.set(1, 1, 1);
    scene.add(light);

    // === 渲染循环 ===
    function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();
    </script>
  </div>
"""
    return js_renderer
